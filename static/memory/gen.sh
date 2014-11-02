#!/bin/bash



inf=$1
of=$2

geom=`gs -q -sDEVICE=bbox \
             -dBATCH -dNOPAUSE -r150 \
             -dLastPage=1 $inf 2>&1 | grep '%%Bou'`
geom=${geom/"%%BoundingBox: "/}
arr=($geom)
x1=${arr[0]}
y1=${arr[1]}
x2=${arr[2]}
y2=${arr[3]}

gs -o $of                                                \
   -sDEVICE=pngalpha -dLastPage=1 -r150                  \
   -dDEVICEWIDTHPOINTS=$[x2-x1]                          \
   -dDEVICEHEIGHTPOINTS=$[y2-y1]                         \
   -dFIXEDMEDIA                                          \
   -c "<</Install {-$x1 -$y1 translate}>> setpagedevice" \
   -f $inf

   
