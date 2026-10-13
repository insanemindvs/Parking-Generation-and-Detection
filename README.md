# Parking-Generation-and-Detection
- An adaptive parking availability system engineered for unstructured, unpainted terrain using standard camera feeds.
- Projects trapezoidal perspective camera views into normalized 2D Cartesian grids for intuitive frontend display.
- Dynamically calibrates slot dimensions based on the pixel footprint of the first parked anchor vehicle.

Open VS Code,
Enter the unzipped folder into VS Code
and open the terminal
then into the terminal paste:
".\venv\Scripts\activate"

Create a .env file
and add these two lines
SUPABASE_URL = 'add your url here'
SUPABASE_KEY = 'add your key here'
Supabase is a free tool for database management, and you can find tutorials for the same

To use this, you need to get some libraries:
So paste the following in your terminal:
"pip install opencv-python ultralytics shapely supabase python-dotenv"

then,
Paste into the terminal
"python main.py"

Wait for a few seconds, it is slightly heavy.
Also, i have pasted all this because I am nervous about adding an .env file
