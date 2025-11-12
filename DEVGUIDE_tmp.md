Robotmk Bridge uses [`invoke`](https://www.pyinvoke.org/) for common tasks:

```bash
invoke --list
invoke test
```

You can also run Robot Framework acceptance suites under `tests/` to validate changes end-to-end.




Clone the repository and install the development dependencies:

```bash
pip install -r requirements.txt
pip install -e .
```