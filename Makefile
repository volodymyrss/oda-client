dist:
	python setup.py sdist bdist_wheel

upload: dist
	twine upload --verbose --skip-existing -r oda dist/*
