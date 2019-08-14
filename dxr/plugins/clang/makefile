CLANG_CXX ?= clang++
ifeq ($(findstring clang++,$(CLANG_CXX)),)
$(error CLANG_CXX is not a version of clang++ : $(CLANG_CXX).)
endif
SUFFIXD = $(subst clang++,,$(CLANG_CXX))
SUFFIX = $(subst -,,$(SUFFIXD))
CLANG_CC ?= $(addsuffix $(SUFFIXD),clang)
LLVM_CONFIG ?= $(addsuffix $(SUFFIXD),llvm-config)
LLVM_LDFLAGS := $(shell ${LLVM_CONFIG} --ldflags)
ifeq ($(LLVM_LDFLAGS),)
$(error Could not run $(LLVM_CONFIG).  Please make sure it is available on your PATH \
or specify the absolute path of the llvm-config executable in the LLVM_CONFIG environment variable)
endif
CXXFLAGS := $(shell ${LLVM_CONFIG} --cxxflags) -std=c++11 -Wall -Wno-strict-aliasing $(if $(DEBUG),-O0 -g)
LDFLAGS := -fPIC -g -Wl,-R -Wl,'$$ORIGIN' $(LLVM_LDFLAGS) -shared
BUILD_DIR_PREFIX = BUILD
BUILD_DIR = $(subst clang++,$(BUILD_DIR_PREFIX),$(CLANG_CXX))
$(shell mkdir -p $(BUILD_DIR))

build: libclang$(SUFFIX)-index-plugin.so


$(BUILD_DIR)/%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $^ -o $@

libclang$(SUFFIX)-index-plugin.so: $(BUILD_DIR)/dxr-index.o $(BUILD_DIR)/sha1.o
	$(CXX) $(LDFLAGS) $^ -o $@

check: build
	which $(CLANG_CC)
	which $(CLANG_CXX)

clean:
	$(RM) -r $(BUILD_DIR_PREFIX)*
	$(RM) libclang*-index-plugin.so

.PHONY: build check clean
