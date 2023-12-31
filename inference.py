import numpy as np
import matplotlib.pyplot as plt
import os
from tqdm import tqdm
import torch
from torch.utils.data import Dataset, DataLoader
# from transformers import SamModel, SamProcessor
# from PIL import Image
# from skimage import transform, io, segmentation
from segment_anything import sam_model_registry
from segment_anything.utils.transforms import ResizeLongestSide
# from torch.nn.utils.rnn import pad_sequence
# from torch.nn import functional as F
# import re
from datasets import NpzDataset
import random
import argparse
from utils import *
from evaluation import *


def segment_data(data):

    dataset = NpzDataset(data)
    data_dataloader = DataLoader(dataset, batch_size=1, shuffle=True)

    dice_coefs, IoU_scores = [], []
    for i, batch in tqdm(enumerate(data_dataloader)):

        batched_output = sam([batch], multimask_output=False)

        img_num = batch['img_num'].item()
        img_path = f"dataset/{data}/images/{data}_{img_num}.png"
        label_path = f"dataset/{data}/labels/{data}_{img_num}.png"
        label = io.imread(label_path)
        pred_mask = batched_output[0]['masks'][0].squeeze().numpy()
    
        # randomly pick few images to qualitatively check the model performance
        # the images are saved in sample_images folder
        if random.randint(1, 100) < 3:
            # side_by_side(img_path, label_path, img_num)
            superpose_img_label(img_path, label_path, img_num)
            superpose_img_mask(img_path, label_path, pred_mask, img_num) # first mask of the first output

        
        # if i == 100: break
        dice_coef = compute_dice_coefficient(label, pred_mask)
        IoU_score = IoU(label, pred_mask)
        dice_coefs.append(dice_coef)
        IoU_scores.append(IoU_score)
        # print(f'{dice_coef=}')
        # break
    avg_dice_coef = sum(dice_coefs) / len(dice_coefs)
    avg_iou_score = sum(IoU_scores) / len(IoU_scores)
    print(f'The average dice coefficient of {data} dataset: {avg_dice_coef}')
    print(f'The intersection over union (IoU) of {data} dataset: {avg_iou_score}')


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=231)
    parser.add_argument("--dataset", type=str, required=True,
                        help='Choose one of the two dataset',
                        choices=('malignant', 'benign'))
    parser.add_argument("--model", type=str, default="vit_h",
                        help='Currently only supports the huge model',
                        choices=("vit_h"))
    parser.add_argument("--use_cpu", action='store_true')

    args = parser.parse_args()
    return args



if __name__ == "__main__":

    args = get_args()
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    models = {
        'vit_h': 'sam_vit_h_4b8939.pth',
        'vit_l': 'sam_vit_l_0b3195.pth',
        'vit_b': 'sam_vit_b_01ec64.pth'
    }

    model_type = args.model
    model = models[model_type]
    device = "cuda" if not args.use_cpu else "cpu"
    sam_checkpoint = f"models/{model}"

    sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
    resize_transform = ResizeLongestSide(sam.image_encoder.img_size)
    segment_data(args.dataset)