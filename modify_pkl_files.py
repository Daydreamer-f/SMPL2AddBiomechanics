#!/usr/bin/env python3
"""
修改examples_mgptout文件夹中的pkl文件
1. 将betas从(72, 10)改为(1, 10)，使用mean操作
2. 添加mocap_framerate键，值为120.0
"""

import pickle
import numpy as np
import os
import glob

def modify_pkl_file(file_path):
    """修改单个pkl文件"""
    print(f"正在处理文件: {file_path}")
    
    # 读取原始数据
    with open(file_path, 'rb') as f:
        data = pickle.load(f)
    
    # 显示原始betas信息
    print(f"  原始betas形状: {data['betas'].shape}")
    print(f"  原始betas类型: {data['betas'].dtype}")
    
    # 修改1: 将betas改为均值
    data['betas'] = data['betas'].mean(axis=0).astype(np.float32)
    print(f"  修改后betas形状: {data['betas'].shape}")
    print(f"  修改后betas类型: {data['betas'].dtype}")
    
    # 修改2: 添加mocap_framerate
    data['mocap_framerate'] = np.float32(120.0)
    print(f"  添加mocap_framerate: {data['mocap_framerate']}")
    
    # 保存修改后的文件
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)
    
    print(f"  文件 {file_path} 修改完成\n")

def main():
    # 获取examples_mgptout文件夹中所有的pkl文件
    pkl_files = glob.glob("examples_mgptout/*.pkl")
    
    if not pkl_files:
        print("在examples_mgptout文件夹中没有找到pkl文件")
        return
    
    print(f"找到 {len(pkl_files)} 个pkl文件:")
    for file in pkl_files:
        print(f"  - {file}")
    print()
    
    # 修改每个文件
    for pkl_file in pkl_files:
        modify_pkl_file(pkl_file)
    
    print("所有文件修改完成!")
    
    # 验证修改结果
    print("\n验证修改结果:")
    for pkl_file in pkl_files:
        with open(pkl_file, 'rb') as f:
            data = pickle.load(f)
        print(f"{pkl_file}:")
        print(f"  betas形状: {data['betas'].shape}")
        print(f"  mocap_framerate: {data.get('mocap_framerate', '未找到')}")

if __name__ == "__main__":
    main()