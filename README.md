# imagetiler
Python module to generate randomly selected image tiles from a set of images


Example: use the demo.py script to extract 10 tiles of dims 250x250 pixels from each .jpg image in ~/hirise_images/ and save the output tiles to the ./tiles directory, while printing verbose output and overwriting existing tiles: 

```
user@console:imagetiler$ identify ./image.jpg 
./image.jpg JPEG 1102x1172 1102x1172+0+0 8-bit sRGB 146KB 0.000u 0:00.000
```

```
user@console:imagetiler$ python demo.py -v -a 0.05 -e .png ./image.jpg ./tiles/
Collecting up to 10 tiles, dims (256 x 256)
tileid row_start row_stop col_start col_stop percent_seen
0 562 818 641 897 0.0000
1 301 557 531 787 0.0000
2 831 1087 662 918 0.0000
3 677 933 390 646 0.0108
4 481 737 40 296 0.0000
5 890 1146 55 311 0.0000
6 132 388 173 429 0.0000
7 155 411 781 1037 0.0101
8 20 276 433 689 0.0000
9 413 669 292 548 0.0488
Collected 10 of 10 requested tiles
imtiler.masktiler.collect elapsed time: 0.200 seconds
imtiler.util.extract_tiles elapsed time: 0.001 seconds
Saved 10 tiles to ./tile_cache/image
imtiler.util.save_tiles elapsed time: 0.365 seconds
```

Output files:
```
user@console:imagetiler$ ls ./tiles/image/
tile132_173.png tile20_433.png  tile413_292.png tile562_641.png tile831_662.png
tile155_781.png tile301_531.png tile481_40.png  tile677_390.png tile890_55.png
```

```
user@console:imagetiler$ identify ./tiles/image/tile562_641.png
./tiles/image/tile562_641.png PNG 256x256 256x256+0+0 8-bit sRGB 30.7KB 0.000u 0:00.000
```

For more information, peruse the [demo.py](https://github.com/dsmbgu8/imagetiler/blob/master/demo.py) script.
