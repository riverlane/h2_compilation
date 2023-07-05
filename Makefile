# ----------------------------------------------------------------------------#
# --------------- MAKEFILE FOR H2 COMPILATION --------------------------------#
# ----------------------------------------------------------------------------#


# For reference see
# https://gist.github.com/mpneuried/0594963ad38e68917ef189b4e6a269db


# --------------- DECLARATIONS -----------------------------------------------#


.DEFAULT_GOAL := help
.PHONY: help
help: ## List of main goals
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / \
	{printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

ifeq ($(OS),Windows_NT)
  # Windows is not supported!
else
  # Some commands are different in Linux and Mac
  UNAME_S := $(shell uname -s)

  # User's credential will be passed to the image and container
  USERNAME=$(shell whoami)
  USER_UID=$(shell id -u)
  USER_GID=$(shell id -g)
endif

PWD=$(shell pwd)

IMAGENAME=h2-compilation
CONTAINERNAME=h2-compilation

DBUILD=docker build . \
	--file ./environment/Dockerfile \
	--tag ${IMAGENAME} \
	--build-arg USERNAME=${USERNAME} \
	--build-arg USER_UID=${USER_UID} \
	--build-arg USER_GID=${USER_GID}

DRUN=docker run \
	--interactive \
	--privileged \
	--rm \
	--volume ${PWD}:/workdir \
	--workdir /workdir \
	--name=${CONTAINERNAME}

DEXEC=docker exec \
	--interactive \
	$(shell cat container)

PYLINT=pylint \
	--exit-zero \
	--rcfile=.pylintrc \
	src/ >> pylint.log


# --------------- DOCKER STUFF -----------------------------------------------#


.PHONY: build
build: ./environment/Dockerfile ## Build the image
	${DBUILD}

.PHONY: build-nc
build-nc: ./environment/Dockerfile ## Build the image from scratch
	${DBUILD} --no-cache

# --privileged: needed for DGB, but also needed for leaksan,
# so causes a heisenbug: lsan throws a warning, enabling --priv fixes it
container: ## Spin out the container
	# if `build` is put in dependencies then it will cause rerun of `container`,
	# we want it to be blocked by `container` file though
	make build
	${DRUN} \
	--detach \
	--cidfile=container \
	${IMAGENAME} \
	/bin/bash

.PHONY: rshell
rshell: container
	docker exec --privileged -it $(shell cat container) /bin/bash

.PHONY: shell
shell: container
	docker exec -it $(shell cat container) /bin/bash


# --------------- CLEANING ---------------------------------------------------#


.PHONY: clean
clean: dev-clean clean-container ## Clean everything

.PHONY: clean-cache
clean-cache: ## Clean python cache
ifeq ($(UNAME_S),Linux)
	find . -name "__pycache__" -type d -print0 | xargs -r0 -- rm -r
	find . -name "*.pyc" -type f -print0 | xargs -r0 -- rm -r
else
	find . -name "*.pyc" -type f -exec rm -rf {} \;
	find . -name "__pycache__" -type d -exec rm -rf {} \;
endif

.PHONY: clean-container
clean-container: ## Stop and remove the container
	docker ps -q --filter "name=${CONTAINERNAME}" | grep -q . && \
	docker stop ${CONTAINERNAME} || true
	rm -f container

.PHONY: clean-data
clean-data: ## Clean any data
ifeq ($(UNAME_S),Linux)
	find . -name "printed_graph.df" -type f -print0 | xargs -r0 -- rm -r
else
	find . -name "printed_graph.df" -exec rm -rf {} \;
endif
	rm -f *.vcd *.png *.txt

.PHONY: clean-logs
clean-logs: ## Clean logs
	rm -f pylint.log pycodestyle.log


# --------------- DEVELOPMENT ------------------------------------------------#


# Commands from this section are meant to be used ONLY inside of
# the development container via VSCode

.PHONY: dev-clean
dev-clean: clean-cache clean-data clean-logs ## See non-dev version
