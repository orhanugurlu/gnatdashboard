PROJECT       = coverage_exhaustive
EXEC_PATH     = obj/main
TRACE_PATH    = $(EXEC_PATH).trace
GNATCOV_FLAGS = -P$(PROJECT) -c stmt+mcdc

all: build run

build:
	gprbuild -p -P$(PROJECT)

run:
	gnatcov run $(GNATCOV_FLAGS) -o $(TRACE_PATH) ./$(EXEC_PATH)
	gnatcov coverage $(GNATCOV_FLAGS) -a xml $(TRACE_PATH)

clean:
	gprclean -P$(PROJECT)
