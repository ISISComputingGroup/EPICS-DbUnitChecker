
install:
	@echo Nothing to be done for dbunitchecker as pure python
	
ifdef OS
   RM = del \Q
   FixPath = $(subst /,\,$1)
else
   ifeq ($(shell uname), Linux)
      RM = rm -f
      FixPath = $1
   endif
endif


clean:
	$(RM) *.pyc *.pyd *.pyo

.DEFAULT:
	@echo Nothing to be done for dbunitchecker as pure python

.PHONY:
	runtests

runtests:
	$(PYTHON3) run_tests.py
