"""Non-destructive evaluation. Output/cache are private; no original CSV is overwritten."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata as metadata
import itertools
import json
from pathlib import Path
import sys

import numpy as np

MODELS = {'Facenet512': 0.50, 'ArcFace': 0.35}
EXPERIMENTS = {
    'A_baseline': set(),
    'B_without_photo2': {'person_03/photo2.jpg'},
    'C_without_test4': {'person_03/test4.jpg'},
    'D_without_both': {'person_03/photo2.jpg', 'person_03/test4.jpg'},
}
EXTENSIONS = {'.jpg', '.jpeg', '.png'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_split(root, name):
    folder = root / name
    if not folder.is_dir():
        return []
    return [dict(split=name, person=p.parent.name, image=p.name,
                 relative=f'{p.parent.name}/{p.name}', path=p, sha256=digest(p))
            for person in sorted(folder.iterdir()) if person.is_dir()
            for p in sorted(person.iterdir()) if p.is_file() and p.suffix.lower() in EXTENSIONS]


def load_datasets(root, validation=False):
    mapping={'dataset':'dataset','test_dataset':'validation_dataset/registered' if validation else 'test_dataset','unknown_dataset':'validation_dataset/unknown' if validation else 'unknown_dataset'}
    result={}
    for canonical, folder in mapping.items():
        rows=load_split(root,folder)
        for row in rows:row['split']=canonical
        result[canonical]=rows
    return result


def audit_splits(splits):
    errors, overlaps = [], []
    labels = {name: {x['person'] for x in rows} for name, rows in splits.items()}
    if not labels['test_dataset'].issubset(labels['dataset']):
        errors.append('Registered test labels must be enrolled reference labels.')
    if labels['unknown_dataset'] & labels['dataset']:
        errors.append('Unknown identity labels overlap enrolled labels.')
    # Byte equality is definitive; decoded equality catches metadata-only copies.
    import cv2
    pixels = {}
    for name, rows in splits.items():
        for item in rows:
            image = cv2.imread(str(item['path']))
            if image is None:
                errors.append(f"Unreadable image: {name}/{item['relative']}")
                continue
            key = hashlib.sha256(str(image.shape).encode() + image.tobytes()).hexdigest()
            for previous in pixels.get(key, []):
                overlaps.append(dict(first=previous, second=f"{name}/{item['relative']}", type='identical_decoded_pixels'))
            pixels.setdefault(key, []).append(f"{name}/{item['relative']}")
    for a, b in itertools.combinations(splits, 2):
        for one in splits[a]:
            for two in splits[b]:
                if one['sha256'] == two['sha256']:
                    overlaps.append(dict(first=f"{a}/{one['relative']}",second=f"{b}/{two['relative']}",type='identical_bytes'))
    cross = [x for x in overlaps if x['first'].split('/')[0] != x['second'].split('/')[0]]
    if cross:
        errors.append('Reference/test/unknown split overlap found; evaluation stopped to prevent leakage.')
    return dict(counts={name:len(rows) for name,rows in splits.items()},
                identities={name:len(labels[name]) for name in splits}, overlaps=overlaps, errors=errors,
                note='Exact byte and decoded-pixel checks do not rule out near duplicates, burst images or shared acquisition sessions.')


def similarity(a, b):
    a,b=np.asarray(a,dtype=float),np.asarray(b,dtype=float)
    if a.ndim!=1 or a.shape!=b.shape or not a.size or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Invalid embeddings')
    norm=np.linalg.norm(a)*np.linalg.norm(b)
    if norm==0: raise ValueError('Zero embedding')
    return float(np.clip(np.dot(a,b)/norm,-1,1))


def metrics(pairs, threshold):
    c=Counter()
    for same,score in pairs:
        c['tp' if same and score>=threshold else 'fn' if same else 'fp' if score>=threshold else 'tn']+=1
    tp,tn,fp,fn=(c[k] for k in ['tp','tn','fp','fn'])
    divide=lambda a,b:a/b if b else None
    precision=divide(tp,tp+fp);recall=divide(tp,tp+fn)
    return dict(threshold=threshold,pairs=len(pairs),tp=tp,tn=tn,fp=fp,fn=fn,
                accuracy=divide(tp+tn,len(pairs)),precision=precision,recall=recall,
                f1=divide(2*tp,2*tp+fp+fn),fmr=divide(fp,fp+tn),fnmr=divide(fn,fn+tp))


def predict(refs, query, threshold):
    ranked=[]
    for row,embedding in refs:
        ranked.append((similarity(embedding,query),row))
    if not ranked:return 'Unavailable',None
    ranked.sort(key=lambda x:(-x[0],x[1]['relative']))
    score,winner=ranked[0]
    if score<threshold:return 'Unknown',score
    tied={row['person'] for value,row in ranked if abs(value-score)<=1e-12}
    duplicate={row['person'] for value,row in ranked if row['sha256']==winner['sha256']}
    if len(tied|duplicate)>1:return 'Ambiguous',score
    return winner['person'],score


def summarize(refs, queries, embeddings, threshold):
    counts=Counter();details=[]
    for item in queries:
        category='unknown' if item['split']=='unknown_dataset' else 'registered'
        vector=embeddings.get((item['split'],item['relative']))
        if vector is None: prediction,score='Failure',None
        else: prediction,score=predict(refs,vector,threshold)
        if prediction in {'Failure','Unavailable'}:outcome='failure'
        elif prediction=='Ambiguous':outcome='ambiguous'
        elif category=='unknown':outcome='correct' if prediction=='Unknown' else 'false_identification'
        else:outcome='correct' if prediction==item['person'] else 'rejected' if prediction=='Unknown' else 'wrong'
        counts[f'{category}_{outcome}']+=1;counts[f'{category}_total']+=1
        details.append(dict(category=category,image=item['relative'],actual=item['person'],prediction=prediction,score=score,outcome=outcome))
    result={k:counts[k] for k in ['registered_total','registered_correct','registered_wrong','registered_rejected','registered_ambiguous','registered_failure','unknown_total','unknown_correct','unknown_false_identification','unknown_ambiguous','unknown_failure']}
    result['registered_accuracy']=counts['registered_correct']/counts['registered_total'] if counts['registered_total'] else None
    result['unknown_rejection_rate']=counts['unknown_correct']/counts['unknown_total'] if counts['unknown_total'] else None
    return result,details


def encode(item, model, cache):
    version=metadata.version('deepface')
    key=hashlib.sha256(f"{model}|{version}|retinaface|align=True|base|{item['sha256']}".encode()).hexdigest()
    cached=cache/(key+'.npy')
    if cached.is_file():vector=np.load(cached,allow_pickle=False)
    else:
        from deepface import DeepFace
        result=DeepFace.represent(img_path=str(item['path']),model_name=model,
            detector_backend='retinaface',align=True,enforce_detection=True,normalization='base')
        if len(result)!=1:raise ValueError(f'Expected one face; detected {len(result)}')
        vector=np.asarray(result[0]['embedding'],dtype=float)
        if vector.shape!=(512,) or not np.isfinite(vector).all() or np.linalg.norm(vector)==0:
            raise ValueError('Invalid 512-value embedding')
        cache.mkdir(parents=True,exist_ok=True)
        np.save(cached,vector,allow_pickle=False)
    if vector.shape!=(512,) or not np.isfinite(vector).all() or np.linalg.norm(vector)==0:
        raise ValueError('Invalid cached embedding; remove only this run cache and rerun')
    return vector


def save_csv(path,rows):
    if not rows:return
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--models',nargs='+',choices=list(MODELS),default=list(MODELS))
    parser.add_argument('--audit-only',action='store_true')
    parser.add_argument('--validation',action='store_true',help='Use validation_dataset/registered and unknown; baseline only, no tuning.')
    args=parser.parse_args()
    output=args.output or Path(__file__).resolve().parents[1]/'outputs'/('evaluation_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output.mkdir(parents=True,exist_ok=False)
    root=args.data_root.resolve()
    if args.validation:
        folders=['dataset','validation_dataset/registered','validation_dataset/unknown']
        counts={name:sum(1 for person in (root/name).iterdir() if person.is_dir()
                        for image in person.iterdir() if image.is_file() and image.suffix.lower() in EXTENSIONS)
                if (root/name).is_dir() else 0 for name in folders}
        if any(count==0 for count in counts.values()):
            (output/'audit.json').write_text(json.dumps(dict(source='independent_validation_candidate',counts=counts,errors=['Required validation/reference split is empty.'],image_overlap_audit='not run because mandatory split is empty'),indent=2))
            raise SystemExit('Dataset empty or audit failed; see audit.json. No model metrics produced.')
    splits=load_datasets(root,args.validation)
    audit_inputs=dict(splits)
    if args.validation:
        # Reusing exploratory queries does not constitute independent validation.
        audit_inputs['prior_registered']=load_split(root,'test_dataset')
        audit_inputs['prior_unknown']=load_split(root,'unknown_dataset')
    audit=audit_splits(audit_inputs)
    audit['source']='independent_validation_candidate' if args.validation else 'exploratory_existing_data'
    (output/'audit.json').write_text(json.dumps(audit,indent=2))
    print(json.dumps(audit,indent=2),flush=True)
    manifest=[{k:v for k,v in item.items() if k!='path'} for rows in splits.values() for item in rows]
    (output/'private_manifest.json').write_text(json.dumps(manifest,indent=2))
    if args.audit_only:return
    if audit['errors'] or any(not rows for rows in splits.values()):
        raise SystemExit('Dataset empty or audit failed; see audit.json. No model metrics produced.')
    experiments={'A_baseline':set()} if args.validation else EXPERIMENTS
    available={x['relative'] for x in splits['dataset']}
    missing=set.union(*experiments.values())-available
    if missing:raise SystemExit(f'Ablation references not found: {sorted(missing)}')
    environment={name:metadata.version(name) for name in ['deepface','retina-face','numpy','onnxruntime','opencv-contrib-python-headless']}
    (output/'environment.json').write_text(json.dumps(dict(python=sys.version,packages=environment,normalization='base',align=True,detector='retinaface',thresholds=MODELS),indent=2))
    cache=output.parent/'private_embedding_cache'
    summaries=[];all_details=[];pair_metrics=[];threshold_sweep=[];failures=[]
    for model in args.models:
        vectors={}
        for rows in splits.values():
            for item in rows:
                print(model,item['split'],item['relative'],flush=True)
                try:vectors[(item['split'],item['relative'])]=encode(item,model,cache)
                except Exception as error:
                    failures.append(dict(model=model,split=item['split'],image=item['relative'],error=str(error)))
                    print('FAILED',type(error).__name__,str(error),flush=True)
        references=[(item,vectors[('dataset',item['relative'])]) for item in splits['dataset'] if ('dataset',item['relative']) in vectors]
        for experiment,excluded in experiments.items():
            refs=[(row,v) for row,v in references if row['relative'] not in excluded]
            summary,details=summarize(refs,splits['test_dataset']+splits['unknown_dataset'],vectors,MODELS[model])
            summary=dict(model=model,experiment=experiment,threshold=MODELS[model],active_references=len(refs),reference_failures=len(splits['dataset'])-len(references),**summary)
            summaries.append(summary)
            all_details.extend(dict(model=model,experiment=experiment,**row) for row in details)
        ref_pairs=[(a['person']==b['person'],similarity(va,vb)) for (a,va),(b,vb) in itertools.combinations(references,2)]
        query_pairs=[(item['person']==ref['person'],similarity(vectors[('test_dataset',item['relative'])],v)) for item in splits['test_dataset'] if ('test_dataset',item['relative']) in vectors for ref,v in references]
        for kind,pairs in [('development_reference_pairs',ref_pairs),('registered_test_reference_pairs',query_pairs)]:
            pair_metrics.append(dict(model=model,kind=kind,**metrics(pairs,MODELS[model])))
        if not args.validation:
            threshold_sweep.extend(dict(model=model,selection_data='development_reference_pairs_only',**metrics(ref_pairs,t/100)) for t in range(0,101,5))
    save_csv(output/'summary.csv',summaries);save_csv(output/'details.csv',all_details)
    save_csv(output/'pair_metrics.csv',pair_metrics);save_csv(output/'development_threshold_sweep.csv',threshold_sweep)
    (output/'failures.json').write_text(json.dumps(failures,indent=2))
    print('Saved new evaluation:',output,flush=True)
    print(json.dumps(summaries,indent=2),flush=True)
    if failures:raise SystemExit('Run completed with image/model failures: inspect failures.json; failures remain in query denominators.')


if __name__=='__main__':main()
