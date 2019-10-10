# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = docs
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

apidoc:
	@sphinx-apidoc --separate -f -o "$(SOURCEDIR)" -H API --maxdepth 10 exoscale

publish-doc: apidoc html
	@cd $(BUILDDIR)/html && \
		touch .nojekyll && \
		git init && \
		git add . && \
		git commit -m "Update documentation" && \
		git push -f git@github.com:exoscale/python-exoscale master:gh-pages

serve:
	@python3 -m http.server 8000 --bind 127.0.0.1 --directory $(BUILDDIR)/html
