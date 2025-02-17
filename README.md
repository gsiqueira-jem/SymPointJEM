<h2 align="center">Symbol as Points: Panoptic Symbol Spotting
via Point-based Representation</h2>
<p align="center">
  <img src="assets/framework.png" width="75%">
</p>


## 📋News
- **[2023/03/07]** 📢Our code and model [weight](https://1drv.ms/f/c/95a3500025f26528/Est7Ia9ty65MkK5bFeJISrcBunuRAM1yXeBM3ICFOg_JYQ?e=LrkpKf) is release.
- **[2024/03/01]** 📢Our paper is released in [Arxiv](https://arxiv.org/pdf/2401.10556.pdf), and camera ready version is updated. 
- **[2024/01/16]** 🎊SymPoint is accepted by **ICLR 2024**.

## Setup Instructions by Manjunadh

Instance used: "manjunadh-hightier-4x-a100-80gb-cuda-11-3"(its named 8x accidentally) or "manjunadh-lowtier-4x-t4-cuda-11-3-60gb-ram" (make sure to give 100gb diskspace and more ram for working with huge vol. of data), Image: "Google, Deep Learning VM with CUDA 11.3, M126, Debian 11, Python 3.10. With CUDA 11.3 preinstalled."

Note that the below instructions work on a system that has nvcc version 11.3 in base env but not on a system that has version 12.4
```bash
conda create -n spv1 python=3.8 -y
conda activate spv1
conda install -c nvidia cudatoolkit=11.1 -y
pip install torch==1.10.0+cu111 torchvision==0.11.0+cu111 -f https://download.pytorch.org/whl/torch_stable.html
pip install gdown mmcv==0.2.14 svgpathtools==1.6.1 munch==2.5.0 tensorboard==2.12.0 tensorboardx==2.5.1
python -m pip install 'git+https://github.com/facebookresearch/detectron2.git'

# compile pointops
cd modules/pointops
python setup.py install

# download dataset
python download_data.py
# 6965 train images, 3827 test images, 810 val images (use ```ls -l | wc -l``` to count no of files in directory location from terminal)

# preprocess (convert train, val, testsets to json format data for training and testing.)
python parse_svg.py --split train --data_dir ./dataset/train/train/svg_gt/
python parse_svg.py --split val --data_dir ./dataset/val/val/svg_gt/
python parse_svg.py --split test --data_dir ./dataset/test/test/svg_gt/

#train
bash tools/train_dist.sh # batchsize,workers = (8,4) use abt 10-12GB per GPU across 4 GPU setup
#test
bash tools/test_dist.sh

# Use ```bash tools/test_dist.sh &> output.txt``` to overwrite the terminal to output.txt file instead
```



## 🔧Installation & Dataset
#### Environment

We recommend users to use `conda` to install the running environment. The following dependencies are required:

```bash
conda create -n spv1 python=3.8 -y
conda activate spv1

pip install torch==1.10.0+cu111 torchvision==0.11.0+cu111 -f https://download.pytorch.org/whl/torch_stable.html
pip install gdown mmcv==0.2.14 svgpathtools==1.6.1 munch==2.5.0 tensorboard==2.12.0 tensorboardx==2.5.1 detectron2==0.6
python -m pip install 'git+https://github.com/facebookresearch/detectron2.git'

# compile pointops
cd modules/pointops
python setup.py install
```

#### Dataset&Preprocess

download dataset from floorplan website, and convert it to json format data for training and testing.

```python
# download dataset
python download_data.py
# preprocess
#train, val, test
python parse_svg.py --split train --data_dir ./dataset/train/train/svg_gt/
python parse_svg.py --split val --data_dir ./dataset/val/val/svg_gt/
python parse_svg.py --split test --data_dir ./dataset/test/test/svg_gt/
```

## 🚀Quick Start

```
#train
bash tools/train_dist.sh
#test
bash tools/test_dist.sh
```

## 🔔Note

As the Attention with Connection Module(ACM) and  Contrastive Connection Learning scheme (CCL) are limited for performance, therefore, for simplicity, in this implementation, we abandoned ACM and CCL.



## 📌Citation
If you find our paper and code useful in your research, please consider giving a star and citation.
<pre><code>
    @article{liu2024symbol,
  title={Symbol as Points: Panoptic Symbol Spotting via Point-based Representation},
  author={Liu, Wenlong and Yang, Tianyu and Wang, Yuhan and Yu, Qizhi and Zhang, Lei},
  journal={arXiv preprint arXiv:2401.10556},
  year={2024}
}
</code></pre>