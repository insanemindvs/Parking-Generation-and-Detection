import os
import cv2
import numpy as np
from ultralytics import YOLO
from shapely.geometry import Polygon
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
model = YOLO('yolov8s.pt') 

video_path = r"C:\Users\mixly\OneDrive\Desktop\Parking_AI\testvideo.mp4"
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("CRITICAL ERROR: Cannot open video stream.")
    exit()

is_calibrated = False
parking_spots = {}          
previous_statuses = {}      
TARGET_LENGTH_M = 6.0
TARGET_WIDTH_M = 4.0

BEV_SIZE = 1000
bev_dst_pts = np.float32([[0, BEV_SIZE], [BEV_SIZE, BEV_SIZE], [BEV_SIZE, 0], [0, 0]])

M_transform = None
M_inverse = None

print("System Booting. Entering Observation Phase...")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    image_height, image_width, _ = frame.shape
    results = model(frame, verbose=False)

    if not is_calibrated:
        cv2.putText(frame, "OBSERVATION PHASE: Waiting for Anchor Car...", 
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        
        horizon_y = int(image_height * 0.4)
        
        cam_src_pts = np.float32([
               
            [image_width * 0.2, horizon_y],[0, image_height],                          
            [image_width, image_height],                
            [image_width * 0.8, horizon_y],                        
        ])
        
        M_transform = cv2.getPerspectiveTransform(cam_src_pts, bev_dst_pts)
        M_inverse = cv2.getPerspectiveTransform(bev_dst_pts, cam_src_pts)
        
        for result in results:
            for box in result.boxes:
                if int(box.cls[0]) == 2 and float(box.conf[0]) > 0.40:
                    
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    car_w = x2 - x1
                    car_bottom_center = np.float32([[[x1 + (car_w / 2), y2]]])
                    
                    bev_car_pos = cv2.perspectiveTransform(car_bottom_center, M_transform)
                    
                    car_left = np.float32([[[x1, y2]]])
                    car_right = np.float32([[[x2, y2]]])
                    bev_left = cv2.perspectiveTransform(car_left, M_transform)
                    bev_right = cv2.perspectiveTransform(car_right, M_transform)
                    
                    bev_car_width = np.linalg.norm(bev_left[0][0] - bev_right[0][0])
                    bev_ppm = bev_car_width / 4.0 
                    
                    bev_grid_w = int(TARGET_WIDTH_M * bev_ppm)
                    bev_grid_h = int(TARGET_LENGTH_M * bev_ppm)
                    
                    if bev_grid_w < 10 or bev_grid_h < 10:
                        continue 
                    
                    print(f"Anchor locked. Flooding entire surface area with grids...")
                    
                    rows = BEV_SIZE // bev_grid_h
                    cols = BEV_SIZE // bev_grid_w
                    
                    for r in range(-rows * 2, rows * 4):
                        for c in range(-cols * 4, cols * 4):
                            top_left_x = c * bev_grid_w
                            top_left_y = r * bev_grid_h
                            bot_right_x = top_left_x + bev_grid_w
                            bot_right_y = top_left_y + bev_grid_h
                            
                            bev_rect = np.float32([
                                [[top_left_x, top_left_y]],
                                [[bot_right_x, top_left_y]],
                                [[bot_right_x, bot_right_y]],
                                [[top_left_x, bot_right_y]]
                            ])
                            
                            cam_poly = cv2.perspectiveTransform(bev_rect, M_inverse)
                            
                            pt1 = (int(cam_poly[0][0][0]), int(cam_poly[0][0][1]))
                            pt2 = (int(cam_poly[1][0][0]), int(cam_poly[1][0][1]))
                            pt3 = (int(cam_poly[2][0][0]), int(cam_poly[2][0][1]))
                            pt4 = (int(cam_poly[3][0][0]), int(cam_poly[3][0][1]))
                            
                            points = [pt1, pt2, pt3, pt4]
                            
                            on_screen_x = any(0 <= pt[0] <= image_width for pt in points)
                            below_horizon = all(pt[1] >= horizon_y for pt in points)
                            
                            if on_screen_x and below_horizon:
                                spot_id = f"R{r}_C{c}"
                                parking_spots[spot_id] = Polygon(points)
                                previous_statuses[spot_id] = False

                    is_calibrated = True
                    break 
            if is_calibrated:
                break 

    else:
        car_polygons = []
        for result in results:
            for box in result.boxes:
                if int(box.cls[0]) in [2, 3, 5, 7]: 
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    car_footprint = Polygon([(x1, y2-20), (x2, y2-20), (x2, y2), (x1, y2)])
                    car_polygons.append(car_footprint)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        for spot_id, spot_poly in parking_spots.items():
            is_occupied = False
            
            for car_footprint in car_polygons:
                if car_footprint.intersects(spot_poly):
                    is_occupied = True
                    break

            if is_occupied != previous_statuses[spot_id]:
                supabase.table("parking_status").update({
                    "is_occupied": is_occupied
                }).eq("spot_name", spot_id).execute()
                
                previous_statuses[spot_id] = is_occupied

            display_coords = np.array(spot_poly.exterior.coords, dtype=np.int32)
            color = (0, 0, 255) if is_occupied else (255, 0, 0)
            cv2.polylines(frame, [display_coords], isClosed=True, color=color, thickness=2)

    cv2.imshow("Project VS2602ALPHA", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
