################################################################################
# Copyright 2020 Advanced Micro Devices, Inc. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell cop-
# ies of the Software, and to permit persons to whom the Software is furnished
# to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IM-
# PLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNE-
# CTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
################################################################################

from .Common import globalParameters
from yaml import safe_load

import os

class ReplacementKernels:
    def __init__(self, dirpath, codeObjectVersion):
        self.dirpath = dirpath
        self.codeObjectVersion = codeObjectVersion
        self._cache = None

    @property
    def marker(self):
        if self.codeObjectVersion == 'V3':
            return '.amdhsa_kernel'
        return '.amdgpu_hsa_kernel'

    def getKernelName(self, filename):
        marker = self.marker

        try:
            with open(filename, 'r') as f:
                for line in f:
                    if line.startswith(marker):
                        return line[len(marker):].strip()
        except Exception:
            print(filename)
            raise
        raise RuntimeError("Could not parse kernel name from {}".format(filename))

    @property
    def cache(self):
        if not self._cache:
            self._cache = self.generateCache()
        return self._cache

    def populateCache(self):
        _ = self.cache

    def generateCache(self):
        cache = {}

        for filename in os.listdir(self.dirpath):
            if filename.endswith('.txt'):
                filepath = os.path.join(self.dirpath, filename)
                kernelName = self.getKernelName(filepath)
                if kernelName in cache:
                    raise RuntimeError("Duplicate replacement kernels.  Kernel name: {}, file names: {}, {}".format(kernelName, cache[kernelName], filepath))
                cache[kernelName] = filepath

        return cache

    def get(self, kernelName):
        if kernelName in self.cache:
            return self.cache[kernelName]

        return None

    @classmethod
    def Directory(cls):
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        dirName = 'ReplacementKernels'
        if globalParameters['CodeObjectVersion'] == 'V3':
            dirName += '-cov3'

        return os.path.join(scriptDir, dirName)

    _instance = None
    @classmethod
    def Instance(cls):
        if cls._instance:
            return cls._instance
        return cls(cls.Directory(), globalParameters["CodeObjectVersion"])

    @classmethod
    def Get(cls, kernelName):
        return cls.Instance().get(kernelName)

customKernelDirectory = os.path.join(os.path.dirname(os.path.realpath(__file__)), "CustomKernels")

def getCustomKernelContents(name, directory=customKernelDirectory):
    try:
        with open(os.path.join(directory, name)) as f:
            return f.read()
    except:
        print("ERROR: Failed to find replacement kernel: {}".format(os.path.join(directory, name)))
        return None

def getCustomKernelConfigAndAssembly(name, directory=customKernelDirectory):
    contents  = getCustomKernelContents(name, directory)
    config = ""
    assembly = ""
    inConfig = False
    for line in contents.splitlines():
        if   line == "---": inConfig = True; print("into config")
        elif line == "...": inConfig = False; print("out of config")
        elif      inConfig: config   += line + "\n"
        else              : assembly += line + "\n"

    return (config, assembly)  

def getCustomKernelConfig(name, directory=customKernelDirectory):
    rawConfig, _ = getCustomKernelConfigAndAssembly(name, directory)
    try:
        return safe_load(rawConfig)["custom.config"]
    except:
        print("ERROR: Failed to read configuration for replacement kernel: {}".format(name))

def getCustomKernelSourceAndMetadata(name, directory=customKernelDirectory):
    return None