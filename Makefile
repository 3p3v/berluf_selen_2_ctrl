build_and_publish:
	python setup.py sdist
	twine upload dist/*