import torch
from torch import nn
from torch.nn import functional as F


class ConvolutionalLayer(nn.Sequential):
    '''
    Simple convolutional layer: input -> conv2d -> activation -> batch norm 2d
    '''
    def __init__(
            self, in_channels, out_channels,
            kernel_size=3, stride=1, padding=0,
            bias=False, activation=nn.LeakyReLU
    ):
        super(ConvolutionalLayer, self).__init__()
        self.add_module(
            "main",
            nn.Sequential(
                nn.Conv2d(
                    in_channels=in_channels,
                    out_channels=out_channels,
                    kernel_size=kernel_size,
                    stride=stride,
                    padding=padding,
                    bias=bias
                ),
                activation(inplace=True),
                nn.BatchNorm2d(num_features=out_channels)
            )
        )



class Flatten(nn.Module):
    def forward(self, input):
        return input.view(input.size(0), -1)



class ResizeConvolutionalLayer(nn.Module):
    '''
    Upsample the image (using an interpolation algorithm), then pass to a conv layer
    '''
    def __init__(self, in_channels, out_channels, mode='bilinear'):
        super(ResizeConvolutionalLayer, self).__init__()
        self._mode = mode
        self.add_module(
            "conv",
            nn.Conv2d(
                in_channels=in_channels,
                out_channels=out_channels,
                kernel_size=3,
                padding=1
            )
        )

    def forward(self, input, out_h, out_w):
        upsampled = F.interpolate(input, size=(out_h, out_w), mode=self._mode)
        return self._modules["conv"](upsampled)


class Reshape(nn.Module):
    def forward(self, input, new_shape):
        return input.view(new_shape)
