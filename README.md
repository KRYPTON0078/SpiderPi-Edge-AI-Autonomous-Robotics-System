# SpiderPi-Edge-AI-Autonomous-Robotics-System

<h1 align="center">SpiderPi Edge-AI Autonomous Robotics System</h1>

<p align="center">
  <b>Autonomous navigation, edge computer vision, gesture interaction, phone-based control, and IoT-style robot monitoring using a SpiderPi hexapod platform.</b>
</p>

<p align="center">
  <a href="https://github.com/KRYPTON0078">GitHub</a> |
  <a href="https://www.linkedin.com/in/magne-dina-neves-86b164322">LinkedIn</a>
</p>

<hr>

<h2>Project Overview</h2>

<p>
  This project extends the SpiderPi hexapod robot into an edge-AI autonomous robotics system.
  It integrates real-time computer vision, gesture recognition, obstacle avoidance, phone-browser control,
  voice commands, camera streaming, and mission planning. The goal was to demonstrate how AI, robotics,
  IoT, and cyber-physical systems can work together to support safer and more intelligent autonomous operation
  in physical environments.
</p>

<p>
  The project was presented at the IoT Data Hackathon 2026 in Hong Kong, where it won first place in the
  Robotics category.
</p>

<h2>Key Features</h2>

<ul>
  <li><b>Autonomous navigation:</b> SpiderPi movement control using forward, back, left, right, stand, stop, patrol, wave, dance, and kick actions.</li>
  <li><b>Obstacle avoidance:</b> Sonar-based avoidance mode for safer movement in physical environments.</li>
  <li><b>Computer vision:</b> Real-time camera processing using OpenCV and the SpiderPi vision modules.</li>
  <li><b>Gesture recognition:</b> Custom CNN-based gesture model trained with TensorFlow/Keras and exported to TensorFlow Lite for edge deployment.</li>
  <li><b>Phone control interface:</b> Mobile browser UI for controlling the robot over the same Wi-Fi network.</li>
  <li><b>Voice command support:</b> Browser-based voice input mapped to robot commands such as forward, left, right, stop, wave, dance, kick, and patrol.</li>
  <li><b>Live camera stream:</b> MJPG camera preview for monitoring robot behavior remotely.</li>
  <li><b>AI mission commander:</b> Prompt-based mission planning with optional cloud AI support and local heuristic fallback.</li>
</ul>

<h2>System Architecture</h2>

<table>
  <tr>
    <th>Layer</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><b>Robot Platform</b></td>
    <td>SpiderPi hexapod robot with camera, servo movement, sonar sensor, and built-in action groups.</td>
  </tr>
  <tr>
    <td><b>Robot Core</b></td>
    <td><code>SpiderPi.py</code> starts camera processing, RPC control, MJPG streaming, sonar access, and robot function modules.</td>
  </tr>
  <tr>
    <td><b>Control Bridge</b></td>
    <td><code>phone_control_server.py</code> serves the phone UI and forwards commands to the SpiderPi JSON-RPC server.</td>
  </tr>
  <tr>
    <td><b>AI / Vision</b></td>
    <td>OpenCV, TensorFlow/Keras, TensorFlow Lite, gesture dataset collection, preprocessing, training, and edge inference workflow.</td>
  </tr>
  <tr>
    <td><b>User Interface</b></td>
    <td>Mobile browser interface for touch control, voice commands, mission planning, and camera preview.</td>
  </tr>
</table>

<h2>Technical Stack</h2>

<ul>
  <li><b>Languages:</b> Python, HTML, CSS, JavaScript</li>
  <li><b>AI / ML:</b> TensorFlow, Keras, TensorFlow Lite, NumPy</li>
  <li><b>Computer Vision:</b> OpenCV, camera calibration, image preprocessing</li>
  <li><b>Robotics:</b> SpiderPi hexapod, servo action groups, sonar-based avoidance, inverse-kinematics-based movement</li>
  <li><b>Networking:</b> JSON-RPC, HTTP server, MJPG camera stream, phone-browser control over Wi-Fi</li>
</ul>

<h2>Core Components</h2>

<ul>
  <li><code>SpiderPi.py</code> - main robot runtime that loads camera, RPC server, MJPG stream, sonar, and robot behavior modules.</li>
  <li><code>phone_control_server.py</code> - mobile control bridge for touch commands, voice commands, mission planning, and robot command routing.</li>
  <li><code>DEMO_SETUP.md</code> - setup guide for running the robot-side control system and phone interface.</li>
  <li><code>SpiderPiGesture/collect_images.py</code> - captures gesture images for dataset creation.</li>
  <li><code>SpiderPiGesture/train.py</code> - trains a CNN gesture classifier using TensorFlow/Keras.</li>
  <li><code>SpiderPiGesture/export_tflite.py</code> - converts the trained model into TensorFlow Lite for lightweight edge deployment.</li>
</ul>

<h2>Gesture Recognition Pipeline</h2>

<ol>
  <li>Collect gesture images using the robot or local camera.</li>
  <li>Preprocess images into a structured dataset.</li>
  <li>Train a CNN model using TensorFlow/Keras.</li>
  <li>Export the trained model to TensorFlow Lite.</li>
  <li>Deploy the lightweight model for edge-AI interaction with the SpiderPi robot.</li>
</ol>

<h2>Phone And Voice Control</h2>

<p>
  The robot can be controlled through a phone browser connected to the same Wi-Fi network.
  The phone UI sends high-level commands to a Python control server, which forwards them to the
  SpiderPi JSON-RPC interface. Supported commands include:
</p>

<ul>
  <li><code>stand</code></li>
  <li><code>forward</code></li>
  <li><code>back</code></li>
  <li><code>left</code></li>
  <li><code>right</code></li>
  <li><code>stop</code></li>
  <li><code>wave</code></li>
  <li><code>dance</code></li>
  <li><code>kick</code></li>
  <li><code>patrol</code></li>
</ul>

<h2>AI Mission Commander</h2>

<p>
  The project includes an AI mission commander concept where a user can describe a task in natural language,
  such as:
</p>

<blockquote>
  Patrol with obstacle avoidance for 40 seconds, then wave and stand.
</blockquote>

<p>
  If an API key is available, the system can use a cloud AI planner. If not, it falls back to a local heuristic
  planner, allowing the robot to continue operating without depending completely on external services.
</p>

<h2>Research Relevance</h2>

<p>
  This project connects robotics, edge AI, IoT, and cyber-physical systems. It demonstrates my interest in
  building intelligent systems that can perceive their environment, make decisions, and interact safely with the
  physical world. The same principles are relevant to trustworthy AI and digital trust research: systems must be
  explainable, resilient, adaptive, and robust against uncertainty or adversarial conditions.
</p>

<h2>Achievement</h2>

<ul>
  <li><b>First Place, Robotics Category</b> - IoT Data Hackathon 2026, Hong Kong.</li>
  <li>Built and demonstrated an AI-enabled SpiderPi robotics system combining autonomous navigation, edge vision, and IoT-style monitoring.</li>
</ul>






<h2>Author</h2>

<p>
  <b>Magne Dina Neves</b><br>
  Electrical and Computer Engineering Student, University of Macau<br>
 
</p>
