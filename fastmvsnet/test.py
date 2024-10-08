#!/usr/bin/env python
import argparse
import os.path as osp
import logging
import time
import sys
sys.path.insert(0, osp.dirname(__file__) + '/..')

import torch
import torch.nn as nn

from fastmvsnet.config import load_cfg_from_file
from fastmvsnet.utils.io import mkdir
from fastmvsnet.utils.logger import setup_logger
from fastmvsnet.model import build_pointmvsnet as build_model
from fastmvsnet.utils.checkpoint import Checkpointer
from fastmvsnet.dataset import build_data_loader
from fastmvsnet.utils.metric_logger import MetricLogger
from fastmvsnet.utils.eval_file_logger import eval_file_logger


def parse_args():
    parser = argparse.ArgumentParser(description="PyTorch Fast-MVSNet Evaluation")
    parser.add_argument(
        "--cfg",
        dest="config_file",
        default="",
        metavar="FILE",
        help="path to config file",
        type=str,
    )
    parser.add_argument(
        "--cpu",
        action='store_true',
        default=False,
        help="whether to only use cpu for test",
    )
    parser.add_argument(
        "opts",
        help="Modify config options using the command-line",
        default=None,
        nargs=argparse.REMAINDER,
    )

    args = parser.parse_args()
    return args


def test_model(model,
               image_scales,
               inter_scales,
               data_loader,
               folder,
               isCPU=False,
               ):
    logger = logging.getLogger("fastmvsnet.train")
    meters = MetricLogger(delimiter="  ")
    model.train()
    end = time.time()
    total_iteration = data_loader.__len__()
    path_list = []
    with torch.no_grad():
        for iteration, data_batch in enumerate(data_loader):
            data_time = time.time() - end
            curr_ref_img_path = data_batch["ref_img_path"][0]
            path_list.extend(curr_ref_img_path)
            if not isCPU:
                data_batch = {k: v.cuda(non_blocking=True) for k, v in data_batch.items() if isinstance(v, torch.Tensor)}
            preds = model(data_batch, image_scales, inter_scales, isGN=True, isTest=True)

            batch_time = time.time() - end
            end = time.time()
            meters.update(time=batch_time, data=data_time)
            logger.info(
                "{} finished.".format(curr_ref_img_path) + str(meters))
            eval_file_logger(data_batch, preds, curr_ref_img_path, folder)



def test(cfg, output_dir, isCPU=False):
    logger = logging.getLogger("fastmvsnet.tester")
    
    # step: 1 build model
    model, _, _ = build_model(cfg)
    if not isCPU:
        model = nn.DataParallel(model).cuda()

    # step: 2 build checkpointer
    checkpointer = Checkpointer(model, save_dir=output_dir)

    if cfg.TEST.WEIGHT:
        weight_path = cfg.TEST.WEIGHT.replace("@", output_dir)
        checkpointer.load(weight_path, resume=False)
    else:
        checkpointer.load(None, resume=True)

    # step: 3 build data loader
    test_data_loader = build_data_loader(cfg, mode="test")


    start_time = time.time()
    test_model(model,
               image_scales=cfg.MODEL.TEST.IMG_SCALES,
               inter_scales=cfg.MODEL.TEST.INTER_SCALES,
               data_loader=test_data_loader,
               folder=output_dir.split("/")[-1],
               isCPU=isCPU,
               )
    
    # step: 4 耗时
    test_time = time.time() - start_time
    logger.info("Test forward time: {:.2f}s".format(test_time))


def main():
    # step: 1 解析命令行
    args = parse_args()
    num_gpus = torch.cuda.device_count()

    # step: 2 导入配置文件
    cfg = load_cfg_from_file(args.config_file)
    cfg.merge_from_list(args.opts)
    cfg.freeze()
    assert cfg.TEST.BATCH_SIZE == 1

    isCPU = args.cpu

    # step: 3 创建输出文件夹
    output_dir = cfg.OUTPUT_DIR
    if output_dir:
        config_path = osp.splitext(args.config_file)[0]
        config_path = config_path.replace("configs", "outputs")
        output_dir = output_dir.replace('@', config_path)
        mkdir(output_dir)

    # step: 4 日志
    logger = setup_logger("fastmvsnet", output_dir, prefix="test")
    if isCPU:
        logger.info("Using CPU")
    else:
        logger.info("Using {} GPUs".format(num_gpus))
    logger.info(args)

    logger.info("Loaded configuration file {}".format(args.config_file))
    logger.info("Running with config:\n{}".format(cfg))

    # step: 5 测试主函数
    test(cfg, output_dir, isCPU=isCPU)


if __name__ == "__main__":
    main()
