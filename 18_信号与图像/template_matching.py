# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / template_matching

本文件实现 template_matching 相关的算法功能。
"""

import numpy as np

def match_template(image, template, method='ssd'):
    ih,iw = image.shape
    th,tw = template.shape
    scores = np.zeros((ih-th+1, iw-tw+1))
    for y in range(ih-th+1):
        for x in range(iw-tw+1):
            patch = image[y:y+th, x:x+tw]
            if method=='ssd':
                scores[y,x] = -np.sum((patch-template)**2)
            elif method=='sad':
                scores[y,x] = -np.sum(np.abs(patch-template))
            elif method=='ncc':
                m1,m2 = np.mean(patch), np.mean(template)
                s1,s2 = np.std(patch)+1e-8, np.std(template)+1e-8
                scores[y,x] = np.sum((patch-m1)*(template-m2))/(s1*s2)
    return scores

def find_peaks(scores, threshold=0.9):
    peaks = []
    h,w = scores.shape
    for y in range(1,h-1):
        for x in range(1,w-1):
            if scores[y,x] >= threshold*scores.max():
                is_peak = True
                for dy in [-1,0,1]:
                    for dx in [-1,0,1]:
                        if dy==0 and dx==0: continue
                        if scores[y,x] < scores[y+dy,x+dx]:
                            is_peak = False
                if is_peak:
                    peaks.append((x,y,scores[y,x]))
    return sorted(peaks, key=lambda p: p[2], reverse=True)

if __name__ == "__main__":
    np.random.seed(42)
    img = np.random.randint(0,256,(50,50))
    template = img[20:28,20:28]
    scores = match_template(img, template, 'ncc')
    peaks = find_peaks(scores, 0.8)
    print(f"Found {len(peaks)} matches, best score: {peaks[0][2]:.4f}" if peaks else "No matches")
    print("\n模板匹配测试完成!")
