#utils_crack_upload.py
import os
import requests
from alibabacloud_imageseg20191230.client import Client
from alibabacloud_imageseg20191230.models import SegmentCommonImageAdvanceRequest
from alibabacloud_tea_openapi.models import Config
from alibabacloud_tea_util.models import RuntimeOptions


def start_segmented_image_upload():
    """
    调用阿里云API进行图像分割，并保存分割后的图像为segmented_image.png

    返回:
        bool: 操作是否成功
        str: 成功时返回图像路径，失败时返回错误信息
    """
    # 配置阿里云API访问密钥
    access_key_id = 'PleaseChangeThis'
    access_key_secret = 'PleaseChangeThis'

    config = Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        endpoint='imageseg.cn-shanghai.aliyuncs.com',
        region_id='cn-shanghai'
    )

    segment_common_image_request = SegmentCommonImageAdvanceRequest()

    # 处理本地图片
    image_path = 'crack.png'
    if not os.path.exists(image_path):
        error_msg = f"图片文件 {image_path} 不存在，请确保文件在同一目录下。"
        print(error_msg)
        return False, error_msg

    try:
        # 打开图片文件
        stream = open(image_path, 'rb')
        segment_common_image_request.image_urlobject = stream
        segment_common_image_request.return_form = ''

        runtime = RuntimeOptions()

        # 初始化Client
        client = Client(config)
        response = client.segment_common_image_advance(segment_common_image_request, runtime)

        result = response.body.to_map()
        print("返回的原始结果：")
        print(result)

        # 分析返回结果
        print("\n返回结果字段分析：")
        print(f"- 顶级字段: {list(result.keys())}")
        if 'Data' in result:
            print(f"- Data字段包含: {list(result['Data'].keys())}")

        # 检查是否有有效的图像URL
        if isinstance(result, dict) and 'Data' in result and 'ImageURL' in result['Data']:
            image_url = result['Data']['ImageURL']
            print(f"获取到图片URL: {image_url[:80]}...")  # 显示部分URL避免过长输出

            if '?Expires=' in image_url:
                print("检测到临时URL(2小时内有效)，立即下载...")

            # 下载分割结果图片
            try:
                print("正在下载分割结果图片...")
                download_response = requests.get(image_url, timeout=15)

                if download_response.status_code == 200:
                    output_path = 'segmented_image.png'
                    with open(output_path, 'wb') as f:
                        f.write(download_response.content)
                    print(f"图片已成功保存到: {output_path}")
                    return True, output_path
                else:
                    error_msg = f"下载失败! HTTP状态码: {download_response.status_code}"
                    print(error_msg)
                    return False, error_msg

            except requests.Timeout:
                error_msg = "下载超时！请检查网络或重试"
                print(error_msg)
                return False, error_msg
            except Exception as download_error:
                error_msg = f"下载过程中发生错误: {str(download_error)}"
                print(error_msg)
                return False, error_msg

        else:
            error_msg = "\nERROR: 返回结果结构异常"
            print(error_msg)
            print("实际返回键值:", list(result.keys()))
            if 'Data' in result:
                print("Data字段中的键:", list(result['Data'].keys()))
            return False, error_msg

    except Exception as api_error:
        error_msg = f"\nAPI调用发生错误: {str(api_error)}"
        print(error_msg)

        # 提取详细错误信息
        error_details = []
        for attr in ['code', 'message', 'data']:
            if hasattr(api_error, attr):
                error_details.append(f"{attr}: {getattr(api_error, attr)}")

        if error_details:
            details = "错误详情:\n" + "\n".join(error_details)
            print(details)
            error_msg += "\n" + details

        return False, error_msg

    finally:
        # 确保关闭文件流
        if 'stream' in locals() and stream and not stream.closed:
            stream.close()
            print("已关闭图片文件流")


# 示例用法
if __name__ == "__main__":
    success, result = start_segmented_image_upload()
    if success:
        print(f"操作成功，分割图像已保存至: {result}")
    else:
        print(f"操作失败: {result}")
