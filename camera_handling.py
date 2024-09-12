from pypylon import pylon


def get_camera():
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    # camera.RegisterConfiguration(
    #     pylon.SoftwareTriggerConfiguration(),
    #     pylon.RegistrationMode_ReplaceAll,
    #     pylon.Cleanup_Delete,
    # )
    return camera


def get_bgr_converter():
    converter = pylon.ImageFormatConverter()
    converter.OutputPixelFormat = pylon.PixelType_BGR8packed
    converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
    return converter


def set_camera_params(camera):
    camera.Open()
    camera.ExposureTime.Value = 1e6  # 1s
    camera.Gain.Value = 0
    camera.Close()


def grab_single_frame(camera):
    camera.Open()
    camera.StartGrabbing()
    grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
    camera.StopGrabbing()
    camera.Close()
    return grabResult


def get_img_from_grab_result(grabResult, converter):
    image = converter.Convert(grabResult)
    img = image.GetArray()
    return img
