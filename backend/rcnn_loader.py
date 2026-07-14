import os
import torch
import torch.nn as nn

# ── Same CNN architecture used during training ────────────────────────────────
class ConvBlock(nn.Module):
    def __init__(self, in_ch, out_ch, stride=1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, stride=stride, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )
    def forward(self, x):
        return self.net(x)


class PotholeCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            ConvBlock(3,   32,  stride=2),
            ConvBlock(32,  64,  stride=2),
            ConvBlock(64,  128, stride=2),
            ConvBlock(128, 256, stride=2),
            ConvBlock(256, 512, stride=2),
        )
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Linear(256, 2)
        )

    def forward(self, x):
        x = self.pool(self.features(x))
        return self.classifier(x.view(x.size(0), -1))


# ── Singleton loader ──────────────────────────────────────────────────────────
_rcnn_model = None

def get_rcnn_model():
    global _rcnn_model
    if _rcnn_model is not None:
        return _rcnn_model

    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rcnn_best.pth')
    if not os.path.exists(model_path):
        print(f"[RCNN] Model file not found at {model_path}")
        return None

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model  = PotholeCNN()
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    _rcnn_model = model
    print(f"[RCNN] Model loaded on {device}")
    return _rcnn_model