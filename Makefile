
install:
	@echo Nothing to be done for dbunitchecker as pure python
	
ifdef OS
   RM = del \Q \S
   FixPath = $(subst /,\,$1)
else
   ifeq ($(shell uname), Linux)
      RM = rm -rf
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
