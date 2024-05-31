#!/bin/sh
# Grid Engine options (lines prefixed with #$)
#$ -N moanet_p2h
#$ -cwd
#$ -pe sharedmem 4
#$ -l h_vmem=64G
#$ -l h_rt=48:00:00
#$ -M L.N.DELONG@sms.ed.ac.uk
#$ -m beas
#$ -o ./eddie_output/
#$ -e ./eddie_output/

# Initialise the environment modules
. /etc/profile.d/modules.sh

# Load Python and corresponding env
module load anaconda
module load python/3.8.17
source activate polo_env

echo $(python --version)

# Run the program
./run.sh configs/MOA-net-p2h.sh
# ./replicates.sh configs/MOA-net-og.sh 5
# ./replicates.sh configs/MOA-net-og-1.sh 5
# ./replicates.sh configs/MOA-net-og-2.sh 5

