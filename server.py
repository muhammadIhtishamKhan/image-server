from sanic import HTTPResponse, Sanic
from sanic.response import text,json
import aiohttp
import asyncio
import cv2 
import numpy as np

app = Sanic("image-server")

async def fetch_image(session,url):
    try:
        async with session.get(url) as response:
            if response.status==200:
                image_data = await response.read()
                image_array= np.frombuffer(image_data,np.uint8)
                return image_array
            else: 
                return None
    except aiohttp.ClientError:
        return None
    
async def fetch_all_images():
    images=[]
    async with aiohttp.ClientSession() as session:
        for offset in range(0,132,10):
            url=f"https://api.slingacademy.com/v1/sample-data/photos?limit=10&offset={offset}"
            try: 
                async with session.get(url) as response:
                    if response.status==200:
                        json_data= await response.json()
                        image_urls= [data["url"] for data in json_data["photos"]]
                   
                        tasks=[fetch_image(session,url) for url in image_urls]
                        fetched_data=await asyncio.gather(*tasks)
                        images.extend(fetched_data)
                    else: 
                        return None
            except Exception as e:
                print("error fetching images from urls", e)
                return None
    return images
        
    
    
def create_composite(images, thumbnail_size=(32,32)):
    try: 
        composite= np.zeros((thumbnail_size[0]*12, thumbnail_size[1]*11, 3), np.uint8)
        row, col = 0, 0
        for image_data in images: 
            if image_data is None:
               
                tile= np.zeros((thumbnail_size[1], thumbnail_size[0], 3), np.uint8)
            else: 
                try:
                    image = cv2.imdecode(image_data,cv2.IMREAD_COLOR)
                  
                    if image is None: 
                        
                        tile= np.zeros((thumbnail_size[1], thumbnail_size[0], 3), np.uint8)
                    else:
                       
                        tile=cv2.resize(image,thumbnail_size)
                except Exception as e:
                    print("error decoding image", e)
                    tile= np.zeros((thumbnail_size[1], thumbnail_size[0], 3), np.uint8)
            composite[row:row+thumbnail_size[1], col:col+thumbnail_size[0]] = tile

            col+= thumbnail_size[0]
            if col >= thumbnail_size[0]*11:
                col=0
                row+= thumbnail_size[1]
        return composite

    except Exception as e:
        print("error creating composite")
        return np.zeros((thumbnail_size[1]*12, thumbnail_size[0]*11, 3), np.uint8)    
@app.get("/")
async def image(request):
    try:
        images = await fetch_all_images()
        composite_image= create_composite(images)
        ret, buffer = cv2.imencode('.jpg', composite_image)
        if ret ==True:
            return HTTPResponse(status=200, body=buffer.tobytes(), content_type='image/jpeg')
        else:
            return HTTPResponse(status=500, body="Error creating composite image from else")
    except Exception as e:
        print(e)
        return HTTPResponse(status=500, body="Error creating composite image")



    
