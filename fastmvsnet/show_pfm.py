#!/usr/bin/env python
import sys
import os.path as osp

sys.path.insert(0, osp.dirname(__file__) + '/..')
import fastmvsnet.utils.io as io
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

def show_pfm_and_xyz(img_fn, pfm_fn, xyz_fn):
    img = mpimg.imread(img_fn)
    depth = io.load_pfm(pfm_fn)[0]
    xyz = np.loadtxt(xyz_fn)

    fig = plt.figure()
    # Display the image
    plt.imshow(img)
    plt.axis('off')  # Optional: Hide axis

    fig, ax = plt.subplots()
    # Display the image
    ax.imshow(depth, cmap='gray')
    ax.set_title("Depth Map")
    ax.axis('off')

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    # Scatter plot for the 3D point cloud
    sc = ax.scatter(xyz[:, 0], xyz[:, 1], xyz[:, 2], c=xyz[:, 2], cmap='jet', marker='o', s=20)

    # Adding color bar
    plt.colorbar(sc)

    # Customize labels and title
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title("3D Point Cloud")

    plt.show()
    plt.close('all')

img_fn = 'data/dtu/Eval/dtu/scan1/00000000.jpg'
pfm_fn = 'data/dtu/Eval/dtu/scan1/00000000_flow2.pfm'
xyz_fn = 'data/dtu/Eval/dtu/scan1/00000000_flow2pts.xyz'
show_pfm_and_xyz(img_fn, pfm_fn, xyz_fn)