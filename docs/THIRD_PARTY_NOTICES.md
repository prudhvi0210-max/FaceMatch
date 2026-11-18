# Third-party software and model provenance

FaceMatch integrates pretrained inference; it does not claim to have trained or
invented FaceNet, ArcFace or RetinaFace. The pinned versions are in the dependency
lockfile. Direct project links:

- [DeepFace](https://github.com/serengil/deepface), version 0.0.104.
- [RetinaFace Python implementation](https://github.com/serengil/retinaface), version 0.0.19.
- [ONNX Runtime](https://github.com/microsoft/onnxruntime).
- [OpenCV](https://opencv.org/), [NumPy](https://numpy.org/),
  [pandas](https://pandas.pydata.org/), [Pillow](https://python-pillow.github.io/).
- Python standard library (SQLite and local HTTP server).

Pretrained model weights are separately downloaded by the libraries and are not
redistributed in this package. Their provenance and applicable model/dataset terms
must be checked for any use beyond this academic prototype; a library's software
license alone is not treated as permission for every pretrained model or dataset.
No new license is imposed on the student's existing code by this completion work.
The academic report cites the primary model papers.
