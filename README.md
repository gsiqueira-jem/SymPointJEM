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
```bash
conda create -n spv1 python=3.8 -y
conda activate spv1
conda install -c nvidia cudatoolkit=11.1
pip install torch==1.10.0+cu111 torchvision==0.11.0+cu111 -f https://download.pytorch.org/whl/torch_stable.html
pip install gdown mmcv==0.2.14 svgpathtools==1.6.1 munch==2.5.0 tensorboard==2.12.0 tensorboardx==2.5.1
python -m pip install 'git+https://github.com/facebookresearch/detectron2.git'

# compile pointops
cd modules/pointops
python setup.py install
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