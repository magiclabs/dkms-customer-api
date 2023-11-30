test-all: test-cdk test-dkms-lambda

PRUN = poetry run

.PHONY: test-cdk
test-cdk:
	$(PRUN) pytest -x tests/

.PHONY: test-dkms-lambda
test-dkms-lambda:
	cd lambdas/dkms_handler && make test

.PHONY: black
black:
	$(PRUN) black .

.PHONY: synth
synth:
	$(PRUN) npx cdk synth

.PHONY: diff
diff:
	$(PRUN) npx cdk diff

.PHONY: list
list:
	$(PRUN) npx cdk list

.PHONY: deploy
deploy:
	$(PRUN) npx cdk deploy

.PHONY: install
install: .install
.install:
	npm install
	poetry install --no-root
	cd lambdas/dkms_handler && poetry install --no-root
	touch .install

.PHONY: clean
clean:
	rm -rf node_modules cdk_out .install
