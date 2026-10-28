"""One-shot held-out test evaluation for completed FoodBD pilot checkpoints."""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw
from torch.utils.data import DataLoader

from foodbd_pilot_common import (
    CHECKPOINTS, CLASSES, DATA, IMAGE_SIZE, MANIFESTS, METRICS, PREDICTIONS,
    SEGMENT_SIZE, UNet, VISUALIZATIONS, FoodBDSet, device, ensure_dirs,
    make_effnet, read_csv, save_json,
)


def sync(dev):
    if dev.type == "cuda":
        torch.cuda.synchronize(dev)


def classification_scores(y: np.ndarray, prob: np.ndarray, thresholds: np.ndarray) -> dict:
    pred = prob >= thresholds[None, :]
    support = y.sum(0).astype(int)
    per_class = []
    f1s, ps, rs = [], [], []
    micro_tp = int((pred & y).sum()); micro_fp = int((pred & ~y).sum()); micro_fn = int((~pred & y).sum())
    for i, name in enumerate(CLASSES):
        yt, yp = y[:, i].astype(bool), pred[:, i]
        tp = int((yt & yp).sum()); fp = int((~yt & yp).sum()); fn = int((yt & ~yp).sum())
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else None
        f = (2 * p * r / (p + r)) if r is not None and p + r else 0.0 if r is not None else None
        per_class.append({"class_id": i, "class_name": name, "support": int(support[i]),
                          "precision": p if support[i] else None,
                          "recall": r, "f1": f, "threshold": float(thresholds[i]),
                          "status": "evaluated" if support[i] else "no_test_positive_support_score_NA"})
        if support[i]: f1s.append(float(f)); ps.append(float(p)); rs.append(float(r))
    micro_p = micro_tp / max(micro_tp + micro_fp, 1)
    micro_r = micro_tp / max(micro_tp + micro_fn, 1)
    micro_f = 2 * micro_p * micro_r / max(micro_p + micro_r, 1e-12)
    macro = {"precision": float(np.mean(ps)), "recall": float(np.mean(rs)), "f1": float(np.mean(f1s)),
             "class_policy": "mean over classes with at least one positive test sample; unsupported class scores are N/A"}
    weighted = {k: float(sum(per_class[i][k] * support[i] for i in range(len(CLASSES)) if support[i]) / support.sum())
                for k in ("precision", "recall", "f1")}
    return {"sample_count": int(len(y)), "subset_accuracy": float(np.all(pred == y, axis=1).mean()),
            "micro": {"precision": micro_p, "recall": micro_r, "f1": micro_f},
            "macro": macro, "weighted": weighted, "per_class": per_class,
            "class_support": {CLASSES[i]: int(support[i]) for i in range(len(CLASSES))},
            "zero_division": 0, "confusion": {CLASSES[i]: {"tp": int((pred[:, i] & y[:, i].astype(bool)).sum()),
                                   "fp": int((pred[:, i] & ~y[:, i].astype(bool)).sum()),
                                   "fn": int((~pred[:, i] & y[:, i].astype(bool)).sum()),
                                   "tn": int((~pred[:, i] & ~y[:, i].astype(bool)).sum())} for i in range(len(CLASSES))},
            "mAP": float(np.mean([average_precision(y[:, i], prob[:, i]) for i in range(len(CLASSES)) if support[i]]))}


def average_precision(y: np.ndarray, score: np.ndarray) -> float:
    """Non-interpolated AP, accumulating precision at tied-score threshold groups."""
    y = y.astype(bool)
    positives = int(y.sum())
    if not positives:
        return float("nan")
    order = np.argsort(-score, kind="mergesort")
    ys, ss = y[order], score[order]
    tp = fp = 0
    ap = 0.0
    prev_recall = 0.0
    start = 0
    while start < len(ys):
        end = start + 1
        while end < len(ys) and ss[end] == ss[start]:
            end += 1
        tp += int(ys[start:end].sum()); fp += (end - start) - int(ys[start:end].sum())
        recall = tp / positives
        precision = tp / max(tp + fp, 1)
        ap += (recall - prev_recall) * precision
        prev_recall = recall
        start = end
    return ap


def evaluate_recognition(dev) -> dict:
    path = CHECKPOINTS / "foodbd_recognition_best.pt"
    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    model = make_effnet(len(CLASSES), pretrained=False)
    model.load_state_dict(ckpt["state_dict"], strict=True); model.to(dev).eval()
    thresholds = np.asarray([x["threshold"] for x in ckpt["thresholds"]], dtype=np.float32)
    rows = [r for r in read_csv(MANIFESTS / "recognition_manifest.csv") if r["split"] == "test"]
    loader = DataLoader(FoodBDSet(rows, "recognition", IMAGE_SIZE), batch_size=16, shuffle=False,
                        num_workers=0, pin_memory=dev.type == "cuda")
    probs, truths = [], []
    sync(dev); t0 = time.perf_counter()
    with torch.inference_mode():
        for x, y in loader:
            p = torch.sigmoid(model(x.to(dev, non_blocking=True))).cpu().numpy()
            probs.append(p); truths.append(y.numpy())
    sync(dev); seconds = time.perf_counter() - t0
    prob, truth = np.concatenate(probs), np.concatenate(truths).astype(bool)
    metrics = classification_scores(truth, prob, thresholds)
    metrics.update({"checkpoint": str(path), "best_epoch": ckpt["epoch"], "inference_seconds_including_image_decode": seconds,
                    "samples_per_second": len(rows) / seconds, "candidate_count": len(rows), "test_split_only": True})
    pred = prob >= thresholds[None, :]
    with (PREDICTIONS / "recognition_test.csv").open("w", encoding="utf-8-sig", newline="") as f:
        import csv
        w = csv.writer(f); w.writerow(["image_id", "true_classes", "predicted_classes", "scores_json", "thresholds_json"])
        for i, row in enumerate(rows):
            w.writerow([row["image_id"], ";".join(CLASSES[j] for j in np.flatnonzero(truth[i])),
                        ";".join(CLASSES[j] for j in np.flatnonzero(pred[i])),
                        json.dumps({CLASSES[j]: round(float(prob[i,j]),6) for j in range(len(CLASSES))}, separators=(",",":")),
                        json.dumps({CLASSES[j]: round(float(thresholds[j]),3) for j in range(len(CLASSES))}, separators=(",",":"))])
    save_json(METRICS / "foodbd_recognition_test.json", metrics)
    return metrics


def evaluate_segmentation(dev) -> dict:
    path = CHECKPOINTS / "foodbd_segmentation_best.pt"
    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    model = UNet(base=16); model.load_state_dict(ckpt["state_dict"], strict=True); model.to(dev).eval()
    rows = [r for r in read_csv(MANIFESTS / "segmentation_manifest.csv") if r["split"] == "test"]
    loader = DataLoader(FoodBDSet(rows, "segmentation", SEGMENT_SIZE), batch_size=12, shuffle=False,
                        num_workers=0, pin_memory=dev.type == "cuda")
    per = []; global_counts = np.zeros(4, dtype=np.int64)
    maskdir = PREDICTIONS / "segmentation/test_masks"; maskdir.mkdir(parents=True, exist_ok=True)
    gtdir = PREDICTIONS / "segmentation/test_ground_truth_masks"; gtdir.mkdir(parents=True, exist_ok=True)
    examples = []
    sync(dev); t0 = time.perf_counter(); offset = 0
    with torch.inference_mode():
        for x, y in loader:
            logits = model(x.to(dev, non_blocking=True)).cpu()
            pred = torch.sigmoid(logits) >= 0.5; truth = y >= 0.5
            for j in range(len(x)):
                p = pred[j,0].numpy(); t = truth[j,0].numpy()
                inter = int(np.logical_and(p,t).sum()); union = int(np.logical_or(p,t).sum())
                pn = int(p.sum()); tn = int(t.sum())
                row = rows[offset+j]
                iou = inter/union if union else 1.0
                dice = 2*inter/(pn+tn) if pn+tn else 1.0
                precision = inter/pn if pn else 0.0; recall = inter/tn if tn else 0.0
                per.append({"image_id":row["image_id"],"iou":iou,"dice":dice,"pixel_precision":precision,
                            "pixel_recall":recall,"predicted_food_pixels":pn,"ground_truth_food_pixels":tn})
                global_counts += [inter,union,pn,tn]
                Image.fromarray((p.astype(np.uint8)*255)).save(maskdir/f"{row['image_id']}.png")
                Image.fromarray((t.astype(np.uint8)*255)).save(gtdir/f"{row['image_id']}.png")
                if len(examples)<6:
                    image=Image.open(DATA/row["image_relpath"]).convert("RGB").resize((SEGMENT_SIZE,SEGMENT_SIZE),Image.Resampling.BILINEAR)
                    examples.append((row["image_id"],image,Image.fromarray(t.astype(np.uint8)*255),Image.fromarray(p.astype(np.uint8)*255)))
            offset += len(x)
    sync(dev); seconds = time.perf_counter()-t0
    inter,union,pn,tn=global_counts.tolist()
    metrics={"checkpoint":str(path),"best_epoch":ckpt["epoch"],"sample_count":len(rows),
             "macro_image_iou":float(np.mean([r['iou'] for r in per])),"macro_image_dice":float(np.mean([r['dice'] for r in per])),
             "global_pixel_iou":inter/max(union,1),"global_pixel_dice":2*inter/max(pn+tn,1),
             "pixel_precision":inter/max(pn,1),"pixel_recall":inter/max(tn,1),"threshold":0.5,
             "inference_seconds_including_image_decode":seconds,"samples_per_second":len(rows)/seconds,
             "target":"binary union of original polygons, food vs background","metrics_policy":"empty-empty per-image mask scores 1; global metrics include all pixels"}
    import csv
    with (PREDICTIONS/"segmentation_test.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(per[0]));w.writeheader();w.writerows(per)
    make_seg_sheet(examples,VISUALIZATIONS/"segmentation_test_examples.png")
    save_json(METRICS/"foodbd_segmentation_test.json",metrics)
    return metrics


def make_seg_sheet(examples, output: Path) -> None:
    cw,ch=300,310; sheet=Image.new("RGB",(cw*3,ch*len(examples)),"white");d=ImageDraw.Draw(sheet)
    for i,(ident,image,truth,pred) in enumerate(examples):
        gt_overlay=image.copy();go=Image.new("RGBA",image.size,(0,0,0,0));go.putalpha(truth.point(lambda p: 90 if p else 0));gt_overlay=Image.alpha_composite(gt_overlay.convert("RGBA"),go).convert("RGB")
        pred_overlay=image.copy();po=Image.new("RGBA",image.size,(255,0,0,0));po.putalpha(pred.point(lambda p: 90 if p else 0));pred_overlay=Image.alpha_composite(pred_overlay.convert("RGBA"),po).convert("RGB")
        for j,(im,title) in enumerate(((image,"image"),(gt_overlay,"GT food overlay"),(pred_overlay,"pred food overlay"))):
            x=j*cw+8;y=i*ch+25;sheet.paste(im.resize((280,260)),(x,y));d.text((x,i*ch+5),f'{ident} {title}',fill='black')
    sheet.save(output)


def regression_metrics(y: np.ndarray, pred: np.ndarray, train: np.ndarray) -> dict:
    result={}
    for j,name in enumerate(("CHO","Protein","Fat")):
        err=pred[:,j]-y[:,j]; baseline=np.median(train[:,j]); berr=baseline-y[:,j]
        denom=float(((y[:,j]-y[:,j].mean())**2).sum())
        result[name]={"mae":float(np.mean(np.abs(err))),"rmse":float(np.sqrt(np.mean(err**2))),
                      "r2":float(1-(err**2).sum()/denom) if len(y)>1 and denom>1e-12 else None,
                      "median_train_baseline":float(baseline),"baseline_mae":float(np.mean(np.abs(berr))),
                      "baseline_rmse":float(np.sqrt(np.mean(berr**2))),"unit":"not specified in source CSV header"}
    return result


def evaluate_nutrition(dev) -> dict:
    path=CHECKPOINTS/"foodbd_nutrition_best.pt";ckpt=torch.load(path,map_location="cpu",weights_only=False)
    model=make_effnet(3,pretrained=False);model.load_state_dict(ckpt["state_dict"],strict=True);model.to(dev).eval()
    rows=read_csv(MANIFESTS/"nutrition_manifest.csv");test_rows=[r for r in rows if r["split"]=="test"];train_rows=[r for r in rows if r["split"]=="train"]
    loader=DataLoader(FoodBDSet(test_rows,"nutrition",IMAGE_SIZE),batch_size=16,shuffle=False,num_workers=0,pin_memory=dev.type=="cuda")
    mean=ckpt["target_mean"].numpy();std=ckpt["target_std"].numpy();outs=[];ys=[]
    sync(dev);t0=time.perf_counter()
    with torch.inference_mode():
        for x,y in loader:
            z=model(x.to(dev,non_blocking=True)).cpu().numpy();outs.append(z*std+mean);ys.append(y.numpy())
    sync(dev);seconds=time.perf_counter()-t0
    pred=np.concatenate(outs);truth=np.concatenate(ys)
    train=np.asarray([[float(r[k]) for k in ("CHO","Protein","Fat")] for r in train_rows],dtype=np.float32)
    metrics={"checkpoint":str(path),"best_epoch":ckpt["epoch"],"sample_count":len(test_rows),
             "inference_seconds_including_image_decode":seconds,"samples_per_second":len(test_rows)/seconds,
             "target_names":["CHO","Protein","Fat"],"target_units":"not stated in source CSV header; values retained unchanged",
             "per_target":regression_metrics(truth,pred,train),
             "label_semantics":"expert-estimated meal/image-level nutrition, not laboratory measurement or per-object target"}
    import csv
    with (PREDICTIONS/"nutrition_test.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.writer(f);w.writerow(["image_id","split","true_CHO","pred_CHO","true_Protein","pred_Protein","true_Fat","pred_Fat"])
        for row,y,p in zip(test_rows,truth,pred):w.writerow([row["image_id"],row["split"],*sum(([float(a),float(b)] for a,b in zip(y,p)),[])])
    save_json(METRICS/"foodbd_nutrition_test.json",metrics)
    return metrics


def main() -> None:
    ensure_dirs();dev=device()
    if dev.type=="cuda":print(f"Test evaluation device: {torch.cuda.get_device_name(0)}")
    # This script is deliberately invoked only after all checkpoint training is complete.
    results={"recognition":evaluate_recognition(dev),"segmentation":evaluate_segmentation(dev),"nutrition":evaluate_nutrition(dev)}
    save_json(METRICS/"foodbd_pilot_test_summary.json",results)
    print(json.dumps({k:{kk:v for kk,v in m.items() if kk in ("sample_count","subset_accuracy","micro","macro","weighted","mAP","macro_image_iou","macro_image_dice","global_pixel_iou","global_pixel_dice","per_target")} for k,m in results.items()},indent=2))


if __name__=="__main__":
    main()
