#!/bin/sh
#set -evx
set -v

##############################
### Paramètres à ajuster
##############################

liste="...indiquer-ici-le-repertoire..../LISTES_RCM/liste_RCM.txt"

## Variable
var="tasAdjust"

domain_model="EURO-CORDEX/EUR-12"
domain_corr="FR-Metro"

type_model="RCM"
corr="MF-CDFt-ANASTASIA-SAFRAN-1985-2014"

## Période totale sur laquelle les données sont lissées
yr1=1951
yr2=2100
## Période de référence pour les anomalies
yr1_ref=1991
yr2_ref=2020

####################################################


while IFS='_' read -r GCM MEM RCM SSP
do

    echo "RCM : $RCM"
    echo "GCM : $GCM"
    echo "MEM : $MEM"
    echo "SSP : $SSP"

	# Chemins des données d'entrée (à compléter)
	pathin="...indiquer-ici-le-repertoire..../${type_model}_CORRIGES/METROPOLE/${domain_model}/${GCM}/${MEM}/${RCM}"

	outputname="${GCM}_${SSP}_${MEM}_${RCM}_${corr}"
        
	# Données historiques (!! à ajuster à la nomenclature des données d'entrée !!)
        file_h=$(ls ${pathin}/historical/day/${var}/version-hackathon-102025/${var}_${domain_corr}_${GCM}_historical_${MEM}_*_${RCM}_*_${corr}_*.nc)

        # Scénario (!! à ajuster à la nomenclature des données d'entrée !!)
        file_s=$(ls ${pathin}/${SSP}/day/${var}/version-hackathon-102025/${var}_${domain_corr}_${GCM}_${SSP}_${MEM}_*_${RCM}_*_${corr}_*.nc)

        # Vérification de l'existence et unicité des fichiers
        for FILE in "$file_h" "$file_s"; do
                # Vérifier si le fichier existe
                if [ ! -n "$FILE" ]; then
                        echo "Erreur : Le fichier $FILE n'existe pas !"
                        exit 1
                fi
        done

        echo $file_h
        echo $file_s

        # Séries annuelle sur le domaine

        cdo mergetime $file_h $file_s tmp0.nc

        cdo seldate,"${yr1}-01-01","${yr2}-12-31" tmp0.nc tmp1.nc
        cdo yearmean tmp1.nc tmp2.nc

        cdo timmean -seldate,"${yr1_ref}-01-01","${yr2_ref}-12-31" tmp0.nc tmpref.nc
        cdo sub tmp2.nc tmpref.nc tmp3.nc

        cdo fldmean tmp3.nc ${var}_1y_${outputname}_time-series-${domain_corr}.nc

        rm -rf tmp*.nc

done < $liste
