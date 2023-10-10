import numpy as np
from tqdm import tqdm
import tensorflow as tf
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, concatenate, Conv2DTranspose, Dropout, UpSampling2D, AveragePooling2D, Reshape, Concatenate, BatchNormalization, Activation

from tensorflow.keras.models import Model
from tensorflow.keras import backend as K
import cv2


def dice_loss(y_true, y_pred):
    smooth = 1e-6 # to avoid division by zero

    
    intersection = tf.reduce_sum(y_true * y_pred, axis=[1,2,3])
    union = tf.reduce_sum(y_true, axis=[1,2,3]) + tf.reduce_sum(y_pred, axis=[1,2,3])
    dice = tf.reduce_mean((2. * intersection + smooth) / (union + smooth))
    return 1. - dice

def jaccard_loss(y_true, y_pred, smooth=1):
    #flatten label and prediction tensors
    inputs = K.flatten(y_pred)
    targets = K.flatten(y_true)
    
    intersection = K.sum(targets * inputs)
    total = K.sum(targets) + K.sum(inputs)
    union = total - intersection
    
    IoU = (intersection + smooth) / (union + smooth)
    return 1 - IoU

def categorical_focal_loss(y_true, y_pred, gamma=2.0, alpha=0.25):

    # Clip the prediction value to prevent NaN's and Inf's
    epsilon = K.epsilon()
    y_pred = K.clip(y_pred, epsilon, 1. - epsilon)

    # Calculate Cross Entropy
    cross_entropy = -y_true * K.log(y_pred)

    # Calculate Focal Loss
    loss = alpha * K.pow(1 - y_pred, gamma) * cross_entropy

    # Compute mean loss in mini_batch
    return K.mean(K.sum(loss, axis=-1))



def jaccard_focal_loss(y_true, y_pred):
    jaccard = jaccard_loss(y_true, y_pred)
    focal = categorical_focal_loss(y_true, y_pred)
    return jaccard + focal




def one_hot_encode_masks(masks, num_classes, label_classes_segments_18):
    """
    :param masks: Y_train patched mask dataset
    :param num_classes: number of classes
    :return:
    """
    # initialise list for integer encoded masks
    integer_encoded_labels = np.zeros((0, masks.shape[1], masks.shape[2], 1), dtype=np.int8)

    # iterate over each mask
    for mask in tqdm(masks):

        # get image shape
        _img_height, _img_width = mask.shape

        # create new mask of zeros
        encoded_image = np.zeros((_img_height, _img_width, 1)).astype(np.int8)

        for j, cls in enumerate(label_classes_segments_18):
            encoded_image[np.all(mask == [j,j,j], axis=-1)] = j

        # append encoded image
        integer_encoded_labels = np.append(integer_encoded_labels, encoded_image.reshape(1,masks.shape[1], masks.shape[2], 1), axis=0)

    # return one-hot encoded labels
    return to_categorical(y=integer_encoded_labels, num_classes=num_classes)


def build_unet(img_shape, n_classes):
    # input layer shape is equal to patch image size
    inputs = Input(shape=img_shape)

    # rescale images from (0, 255) to (0, 1)
    #rescale = Rescaling(scale=1. / 255, input_shape=(img_shape[0], img_shape[1], img_shape[2]))(inputs)
    #previous_block_activation = rescale # Set aside residual
    previous_block_activation = inputs

    contraction = {}
    # # Contraction path: Blocks 1 through 5 are identical apart from the feature depth
    for f in [32, 64, 128, 256]:
        x = Conv2D(f, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(
            previous_block_activation)
        x = Dropout(0.1)(x)
        x = Conv2D(f, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(x)
        contraction[f'conv{f}'] = x
        x = MaxPooling2D((2, 2))(x)
        previous_block_activation = x

    c5 = Conv2D(512, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(
        previous_block_activation)
    c5 = Dropout(0.1)(c5)
    c5 = Conv2D(512, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(c5)
    previous_block_activation = c5

    # Expansive path: Second half of the network: upsampling inputs
    for f in reversed([32, 64, 128, 256]):
        x = Conv2DTranspose(f, (2, 2), strides=(2, 2), padding='same')(previous_block_activation)
        x = concatenate([x, contraction[f'conv{f}']])
        x = Conv2D(f, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(x)
        x = Dropout(0.2)(x)
        x = Conv2D(f, (3, 3), activation='relu', kernel_initializer='he_normal', padding='same')(x)
        previous_block_activation = x

    outputs = Conv2D(filters=n_classes, kernel_size=(1, 1), activation="softmax")(previous_block_activation)

    return Model(inputs=inputs, outputs=outputs)


def iou_coefficient(y_true, y_pred, smooth=1):
    intersection = K.sum(K.abs(y_true * y_pred), axis=[1, 2, 3])
    union = K.sum(y_true, [1, 2, 3]) + K.sum(y_pred, [1, 2, 3]) - intersection
    iou = K.mean((intersection + smooth) / (union + smooth), axis=0)
    return iou






def conv_block(input, num_filters):
    x = Conv2D(num_filters, 3, kernel_initializer='he_normal', padding="same")(input)
    x = BatchNormalization()(x)
    x = Activation("relu")(x)

    x = Conv2D(num_filters, 3, kernel_initializer='he_normal', padding="same")(x)
    x = BatchNormalization()(x)
    x = Activation("relu")(x)

    return x

def decoder_block(input, skip_features, num_filters):
    x = Conv2DTranspose(num_filters, (2, 2), strides=2, padding="same")(input)
    x = Concatenate()([x, skip_features])
    x = conv_block(x, num_filters)
    return x

def build_unet_vgg16(input_shape, n_classes):
    """ Input """
    inputs = Input(input_shape)

    """ Pre-trained VGG16 Model """
    vgg16 = tf.keras.applications.VGG16(include_top=False, weights="imagenet", input_tensor=inputs)

    for layer in vgg16.layers:
        layer.trainable = False

    """ Encoder """
    s1 = vgg16.get_layer("block1_conv2").output         ## (512 x 512)
    s2 = vgg16.get_layer("block2_conv2").output         ## (256 x 256)
    s3 = vgg16.get_layer("block3_conv3").output         ## (128 x 128)
    s4 = vgg16.get_layer("block4_conv3").output         ## (64 x 64)

    """ Bridge """
    b1 = vgg16.get_layer("block5_conv3").output         ## (32 x 32)

    """ Decoder """
    d1 = decoder_block(b1, s4, 512)                     ## (64 x 64)
    d2 = decoder_block(d1, s3, 256)                     ## (128 x 128)
    d3 = decoder_block(d2, s2, 128)                     ## (256 x 256)
    d4 = decoder_block(d3, s1, 64)                      ## (512 x 512)

    """ Output """
    outputs = Conv2D(n_classes, 1, padding="same", activation="softmax")(d4)

    model = Model(inputs, outputs, name="VGG16_U-Net")
    return model


def build_resnet50_unet(input_shape, n_classes):
    """ Input """
    inputs = Input(input_shape)

    """ Pre-trained ResNet50 Model """
    resnet50 = tf.keras.applications.ResNet50(include_top=False, weights="imagenet", input_tensor=inputs)

    for layer in resnet50.layers:
        layer.trainable = False

    """ Encoder """
    s1 = resnet50.get_layer("input_1").output           ## (512 x 512)
    s2 = resnet50.get_layer("conv1_relu").output        ## (256 x 256)
    s3 = resnet50.get_layer("conv2_block3_out").output  ## (128 x 128)
    s4 = resnet50.get_layer("conv3_block4_out").output  ## (64 x 64)

    """ Bridge """
    b1 = resnet50.get_layer("conv4_block6_out").output  ## (32 x 32)

    """ Decoder """
    d1 = decoder_block(b1, s4, 512)                     ## (64 x 64)
    d2 = decoder_block(d1, s3, 256)                     ## (128 x 128)
    d3 = decoder_block(d2, s2, 128)                     ## (256 x 256)
    d4 = decoder_block(d3, s1, 64)                      ## (512 x 512)

    """ Output """
    outputs = Conv2D(n_classes, 1, padding="same", activation="softmax")(d4)

    model = Model(inputs, outputs, name="ResNet50_U-Net")
    return model

def encoder_block(input, num_filters):
    x = conv_block(input, num_filters)
    p = MaxPooling2D((2, 2))(x)
    return x, p



def build_unet1(input_shape, n_classes):
    inputs = Input(input_shape)

    s1, p1 = encoder_block(inputs, 32)
    s2, p2 = encoder_block(p1, 64)
    s3, p3 = encoder_block(p2, 128)
    s4, p4 = encoder_block(p3, 256)

    b1 = conv_block(p4, 512)

    d1 = decoder_block(b1, s4, 256)
    d2 = decoder_block(d1, s3, 128)
    d3 = decoder_block(d2, s2, 64)
    d4 = decoder_block(d3, s1, 32)

    outputs = Conv2D(n_classes, 1, padding="same", activation="softmax")(d4)

    model = Model(inputs, outputs, name="U-Net")
    return model



def edit_image(image, brightness=0, contrast=1.0, saturation=1.0, hue=0, mode='RGB'):
    # Load the image


    # Adjust brightness
    if(mode == 'RGB'):
        hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    elif(mode == 'BGR'):
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hsv_image[..., 2] = np.clip(hsv_image[..., 2] + brightness, 0, 255)

    # Adjust contrast
    adjusted_image = cv2.convertScaleAbs(hsv_image, alpha=contrast, beta=0)

    # Adjust saturation and hue
    adjusted_image[..., 1] = np.clip(adjusted_image[..., 1] * saturation, 0, 255)
    adjusted_image[..., 0] = (adjusted_image[..., 0] + hue) % 180

    # Convert back to BGR color space
    if(mode == 'RGB'):
        edited_image = cv2.cvtColor(adjusted_image, cv2.COLOR_HSV2RGB)
    elif(mode == 'BGR'):
         edited_image = cv2.cvtColor(adjusted_image, cv2.COLOR_HSV2BGR)
    return edited_image

def count_values(I, mode):

    contrast = I.std()

    # Calculate brightness
    brightness = I.mean()

    # Calculate saturation and hue
    if(mode == 'RGB'):
        hsv_image = cv2.cvtColor(I, cv2.COLOR_RGB2HSV)
    elif(mode == 'BGR'):
        hsv_image = cv2.cvtColor(I, cv2.COLOR_BGR2HSV)
    saturation = hsv_image[..., 1].mean()
    hue = hsv_image[..., 0].mean()

    return contrast, brightness, saturation, hue


def preprocessing(I, target_c, target_b, target_s, target_h):

    contrast, brightness, saturation ,hue = count_values(I, mode='RGB')

    I = edit_image(I, 0, target_c/contrast , 1, 0, mode='RGB')

    contrast, brightness, saturation ,hue = count_values(I, mode='RGB')

    I = edit_image(I, target_b - brightness, 1 , 1, 0,  mode='RGB')

    contrast, brightness, saturation ,hue = count_values(I, mode='RGB')

    I = edit_image(I, 0, 1 , target_s/saturation, 0,  mode='RGB')

    contrast, brightness, saturation ,hue = count_values(I, mode='RGB')


    I = edit_image(I, 0, 1, 1, target_h - hue,  mode='RGB')

    contrast, brightness, saturation ,hue = count_values(I, mode='RGB')

    I = tf.keras.applications.resnet50.preprocess_input(I)

    return I
