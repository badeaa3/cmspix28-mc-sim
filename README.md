# Simulations for smart pixels

# Setup
You'll need
* root
* python
* pythia
* hepmc

A few ways to setup are outlined below

## 1. Setting up your environment from scratch

setup root and python
```
setupATLAS
lsetup "python 3.9.18-x86_64-centos7"
lsetup "root 6.28.08-x86_64-centos7-gcc11-opt"
```
get pythia 8.307
in your home directory
```
wget https://pythia.org/download/pythia83/pythia8307.tgz
tar -xvf pythia8307.tgz
cd pythia8307
make
```
check out this repository 
```
cd
git clone --recursive git@github.com:badeaa3/cmspix28-mc-sim.git
cd cmspix28-mc-sim
```
update this package's Makefile.inc to point to your pythia path
`PREFIX=/home/abadea/pythia8307`

compile and run a test
```
make all
./minbias.exe <outFileName> <maxEvents> <pTHatMin> <pTHatMax>
```

## 2. Setting up with docker images on MCP workstation 

check out this repository
```
git clone --recursive git@github.com:badeaa3/cmspix28-mc-sim.git
cd cmspix28-mc-sim
```
setup environment
```
singularity run --nv -e --bind /cvmfs /local/d1/``karri``/quick-start/my-image.sif
```
compile and run a test
```
make all
./minbias.exe <outFileName> <maxEvents> <pTHatMin> <pTHatMax>
```

# To run pixelAV (TBC)
```
cd pixelav
mkdir bin
gcc ppixelav2_list_trkpy_n_2f.c -o ./bin/ppixelav2_list_trkpy_n_2f.exe -lm -O2
cd ..
make
python launch.py -o temp -n 100

```
