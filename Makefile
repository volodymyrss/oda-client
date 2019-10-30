REPO?=oda

dist:
	python setup.py sdist bdist_wheel

upload: dist
	twine upload --verbose --skip-existing -r $(REPO) dist/*

test:
	python -m pytest tests -sv
