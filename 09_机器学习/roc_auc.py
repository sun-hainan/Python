# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / roc_auc



本文件实现 roc_auc 相关的算法功能。

"""



import numpy as np

from typing import Tuple



def roc_curve(y_true, y_scores):

    # roc_curve function



    # roc_curve function

    """Compute ROC curve"""

    indices = np.argsort(y_scores)[::-1]

    y_true_sorted = y_true[indices]

    n_pos = y_true.sum()

    n_neg = len(y_true) - n_pos

    tpr, fpr = [], []

    tp = fp = 0

    for i in range(len(y_true_sorted)):

        if y_true_sorted[i] == 1:

            tp += 1

        else:

            fp += 1

        tpr.append(tp / n_pos)

        fpr.append(fp / n_neg)

    return np.array(fpr), np.array(tpr)



def auc_score(fpr, tpr):

    """Compute AUC using trapezoidal rule"""

    auc = 0.0

    for i in range(len(fpr) - 1):

        auc += (fpr[i+1] - fpr[i]) * (tpr[i] + tpr[i+1]) / 2

    return auc



def confusion_matrix_binary(y_true, y_pred):

    # confusion_matrix_binary function



    # confusion_matrix_binary function

    tp = np.sum((y_true == 1) & (y_pred == 1))

    tn = np.sum((y_true == 0) & (y_pred == 0))

    fp = np.sum((y_true == 0) & (y_pred == 1))

    fn = np.sum((y_true == 1) & (y_pred == 0))

    return {'tp': tp, 'tn': tn, 'fp': fp, 'fn': fn}



def metrics_from_cm(cm):

    # metrics_from_cm function



    # metrics_from_cm function

    tp, tn, fp, fn = cm['tp'], cm['tn'], cm['fp'], cm['fn']

    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0

    recall = tp / (tp + fn) if (tp + fn) > 0 else 0

    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {'accuracy': accuracy, 'precision': precision, 'recall': recall, 'f1': f1}



if __name__ == '__main__':

    print('=== ROC/AUC test ===')

    np.random.seed(42)

    y_true = np.random.randint(0, 2, 200)

    y_scores = np.random.rand(200)

    print(f'Positive rate: {y_true.mean():.2%}')

    fpr, tpr = roc_curve(y_true, y_scores)

    auc = auc_score(fpr, tpr)

    print(f'AUC: {auc:.4f}')

    y_pred = (y_scores > 0.5).astype(int)

    cm = confusion_matrix_binary(y_true, y_pred)

    m = metrics_from_cm(cm)

    print(f'Metrics: accuracy={m["accuracy"]:.4f}, precision={m["precision"]:.4f}, recall={m["recall"]:.4f}, f1={m["f1"]:.4f}')

