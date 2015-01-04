#!/bin/bash

cd db
rm papers.db
./create-database.sh
cd ..

rm static/memory/pdfs/*
rm static/memory/previews/*
mkdir -p static/memory/pdfs
mkdir -p static/memory/previews
mkdir -p logs
