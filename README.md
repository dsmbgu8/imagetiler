# imagetiler
Python module to generate randomly selected image tiles from a set of images


Example: use the demo.py script to extract 10 tiles of dims 250x250 pixels from each .jpg image in ~/hirise_images/ and save the output tiles to the ./tiles directory, while printing verbose output and overwriting existing tiles: 

```
user@console:imagetiler$ python demo.py -v -r -d 250 -n 10 -e .jpg ~/hirise_images/ ./tiles/
```

```
Extracting tiles for 17 images
Image 1 of 17 ESP_027802_1685_RED_A_01_ORTHO.jpg dims= (10000, 10000, 1)
tileid row_start row_stop col_start col_stop percent_masked
0 5420 5670 8260 8510 0.000
1 1780 2030 6820 7070 0.000
2 3750 4000 4280 4530 0.000
3 5070 5320 5560 5810 0.000
4 2240 2490 8260 8510 0.000
5 3990 4240 7110 7360 0.000
6 6590 6840 2450 2700 0.000
7 7780 8030 7240 7490 0.000
8 1920 2170 810 1060 0.000
9 1860 2110 7970 8220 0.000
imtile.imagetiler.collect elapsed time: 0.005 seconds
writing 10 tiles to ./tiles/ESP_027802_1685_RED_A_01_ORTHO
imtile.imagetiler.write elapsed time: 1.876 seconds
...
Image 17 of 17 ESP_d027802_1685_RED_A_01_ORTHO.jpg dims= (10000, 10000, 1)
tileid row_start row_stop col_start col_stop percent_masked
0 9300 9550 3050 3300 0.000
1 220 470 2050 2300 0.000
2 5350 5600 3920 4170 0.000
3 6400 6650 1000 1250 0.000
4 4300 4550 1010 1260 0.000
5 3670 3920 7510 7760 0.000
6 870 1120 3470 3720 0.000
7 7660 7910 7820 8070 0.000
8 4650 4900 2900 3150 0.000
9 9180 9430 4020 4270 0.000
imtile.imagetiler.collect elapsed time: 0.006 seconds
writing 10 tiles to ./tiles/ESP_d027802_1685_RED_A_01_ORTHO
imtile.imagetiler.write elapsed time: 1.952 seconds
Loading image tile collections for 17 images
imtile.tilecollection.load elapsed time: 65.009 seconds
ESP_031059_1685_RED_A_01_ORTHO: 10 tiles of shape (250, 250)
```

Output files:

```
user@console:imagetiler$ ls tiles/
ESP_027802_1685_RED_A_01_ORTHO  ESP_032048_1685_RED_A_01_ORTHO
ESP_028501_1685_RED_A_01_ORTHO  ESP_032615_1685_RED_A_01_ORTHO
ESP_029213_1685_RED_A_01_ORTHO  ESP_032905_1685_RED_A_01_ORTHO
ESP_029780_1685_RED_A_01_ORTHO  ESP_033116_1685_RED_A_01_ORTHO
ESP_030136_1685_RED_A_01_ORTHO  ESP_034184_1685_RED_A_01_ORTHO
ESP_030347_1685_RED_A_01_ORTHO  ESP_034672_1685_RED_A_01_ORTHO
ESP_030769_1685_RED_A_01_ORTHO  ESP_035028_1685_RED_A_01_ORTHO
ESP_031059_1685_RED_A_01_ORTHO  ESP_d027802_1685_RED_A_01_ORTHO
ESP_031771_1685_RED_A_01_ORTHO

user@console:imagetiler$ ls tiles/ESP_027802_1685_RED_A_01_ORTHO/
0.jpg       2.jpg       4.jpg       6.jpg       8.jpg       mask.jpg
1.jpg       3.jpg       5.jpg       7.jpg       9.jpg       tilepos.txt

user@console:imagetiler$ cat tiles/ESP_027802_1685_RED_A_01_ORTHO/tileinfo.txt
tileid row_start row_stop col_start col_stop percent_masked
0 3490 3740 1620 1870 0.000
1 5180 5430 7650 7900 0.000
2 7190 7440 1830 2080 0.000
3 9240 9490 9070 9320 0.000
4 5110 5360 6240 6490 0.000
5 2050 2300 8230 8480 0.000
6 5580 5830 20 270 0.000
7 8650 8900 2610 2860 0.000
8 5620 5870 4850 5100 0.000
9 9180 9430 4670 4920 0.000
```

For more information, peruse the [demo.py](https://github.com/dsmbgu8/imagetiler/blob/master/demo.py) script.
