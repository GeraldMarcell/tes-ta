"""Run the three available FoodBD pilot stages on one image, without ground truth."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw

from foodbd_pilot_common import (
    CHECKPOINTS, CLASSES, IMAGE_SIZE, OUT, SEGMENT_SIZE, UNet, device,
    ensure_dirs, image_tensor, make_effnet,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=OUT / "predictions/integrated_demo")
    args = parser.parse_args()
    if not args.image.is_file():
        parser.error(f"input image not found: {args.image}")
    ensure_dirs(); dev=device(); args.output.mkdir(parents=True,exist_ok=True)
    for name in ("foodbd_recognition_best.pt","foodbd_segmentation_best.pt","foodbd_nutrition_best.pt"):
        if not (CHECKPOINTS/name).is_file(): raise FileNotFoundError(CHECKPOINTS/name)
    rec_ckpt=torch.load(CHECKPOINTS/"foodbd_recognition_best.pt",map_location="cpu",weights_only=False)
    rec=make_effnet(len(CLASSES));rec.load_state_dict(rec_ckpt["state_dict"],strict=True);rec.to(dev).eval()
    seg_ckpt=torch.load(CHECKPOINTS/"foodbd_segmentation_best.pt",map_location="cpu",weights_only=False)
    seg=UNet(base=16);seg.load_state_dict(seg_ckpt["state_dict"],strict=True);seg.to(dev).eval()
    nut_ckpt=torch.load(CHECKPOINTS/"foodbd_nutrition_best.pt",map_location="cpu",weights_only=False)
    nut=make_effnet(3);nut.load_state_dict(nut_ckpt["state_dict"],strict=True);nut.to(dev).eval()
    x=image_tensor(args.image,IMAGE_SIZE).unsqueeze(0).to(dev)
    xs=image_tensor(args.image,SEGMENT_SIZE).unsqueeze(0).to(dev)
    with torch.inference_mode():
        prob=torch.sigmoid(rec(x))[0].cpu().numpy()
        mask=(torch.sigmoid(seg(xs))[0,0]>=0.5).cpu().numpy().astype(np.uint8)
        z=nut(x).cpu().numpy()[0]
    thresholds=np.asarray([x["threshold"] for x in rec_ckpt["thresholds"]])
    selected=np.flatnonzero(prob>=thresholds)
    ranked=np.argsort(-prob)[:5]
    with Image.open(args.image) as im: source=im.convert("RGB")
    input_copy=args.output/"input"/args.image.name;input_copy.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(args.image,input_copy)
    mask_img=Image.fromarray(mask*255).resize(source.size,Image.Resampling.NEAREST)
    mask_path=args.output/"food_mask.png";mask_img.save(mask_path)
    overlay=source.copy().convert("RGBA"); color=Image.new("RGBA",source.size,(255,40,20,0)); color.putalpha(mask_img.point(lambda v:90 if v else 0));overlay=Image.alpha_composite(overlay,color).convert("RGB")
    overlay_path=args.output/"mask_overlay.png";overlay.save(overlay_path)
    mean=nut_ckpt["target_mean"].numpy();std=nut_ckpt["target_std"].numpy();values=(z*std+mean).tolist()
    scores={CLASSES[i]:float(prob[i]) for i in range(len(CLASSES))}
    result={"input_image":str(input_copy),"device":str(dev),"models":{
        "recognition":{"checkpoint":str(CHECKPOINTS/"foodbd_recognition_best.pt"),"selected_classes":[{"class":CLASSES[i],"score":float(prob[i]),"validation_threshold":float(thresholds[i])} for i in selected],
                        "top5_scores":[{"class":CLASSES[i],"score":float(prob[i])} for i in ranked],"all_scores":scores},
        "segmentation":{"checkpoint":str(CHECKPOINTS/"foodbd_segmentation_best.pt"),"task":"binary food/background","threshold":0.5,
                        "predicted_food_fraction":float(mask.mean()),"mask_path":str(mask_path),"overlay_path":str(overlay_path)},
        "nutrition":{"checkpoint":str(CHECKPOINTS/"foodbd_nutrition_best.pt"),"targets":{"CHO":values[0],"Protein":values[1],"Fat":values[2]},
                      "unit":"not specified by source CSV header","semantics":"expert-estimated image-level targets"},
        "portion_weight":{"status":"not_available","reason":"no verified measured-weight target"}},
        "interpretation":"technical inference demo only; not an accuracy claim"}
    (args.output/"prediction.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"output":str(args.output),"selected_classes":result["models"]["recognition"]["selected_classes"],
                      "nutrition":result["models"]["nutrition"]["targets"],"weight_status":"not_available"},indent=2))


if __name__=="__main__":main()
