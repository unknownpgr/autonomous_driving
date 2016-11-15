#!/usr/bin/python
from detectionlib import ImagePreparator
from detectionlib import LineFilter
from detectionlib import LaneDetector
from detectionlib import Visualizer
import rospy
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError

NODE_NAME = "lane_detector"
SUB_TOPIC = "image_resized"
PUB_TOPIC = "debug_image"

class LaneDetectorNode:

	def __init__(self, sub_topic, pub_topic):
		self.act_left_line = [(0,0),(0,0)]
		self.act_right_line = [(0,0),(0,0)]
		self.lane_detector = LaneDetector()
		self.bridge = CvBridge()
		self.image_sub = rospy.Subscriber(sub_topic, Image, self.callback)
		self.image_pub = rospy.Publisher(pub_topic, Image, queue_size=10)
		rospy.spin()

	def callback(self, data):
		try:
			cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
		except CvBridgeError as e:
			rospy.logerr(e)

		# Aufbereitung des Bilder
		img_prep = ImagePreparator(cv_image.copy())
		img_prep.define_roi(0.6,0, 0.25)
		img_prep.filter_white_color(190,255)
		img_prep.grayscale()
		img_prep.morph_open(3)
		img_prep.blur((3,3), 0)
		# Canny oder Threshold benutzen
		#img_prep.global_threshold(165, 255)
		img_prep.canny(50, 150, 3) # (1, 250, 3) oder (50, 150, 3)
		
		# Entdecke Linien
		lines = self.lane_detector.houghlines_p(img_prep.image, 50, 10, 10) # (50, 10, 10) oder (100, 1, 10)
		
		# Filter korrekte Linien
		line_filter = LineFilter(cv_image)
		lines_dic = line_filter.filter_by_angle(lines, 10, 0.6)
		
		new_left_line = lines_dic['left']
		new_right_line = lines_dic['right']

		if len(new_left_line) > 1:
			self.act_left_line = new_left_line
		if len(new_right_line) > 1:
			self.act_right_line = new_right_line

		#vis = Visualizer(img_prep.image)
		vis = Visualizer(cv_image)
		vis.draw_line(self.act_left_line[0], self.act_left_line[1], (0,0,255),3)
		vis.draw_line(self.act_right_line[0], self.act_right_line[1], (0,255,0),3)
		#vis.draw_lines(lines, (0,255,0), 2)
		vis.show()
		# Publish Bild mit den gezeichneten Linien
		try:
			self.image_pub.publish(self.bridge.cv2_to_imgmsg(cv_image, "bgr8"))
		except CvBridgeError as e:
			rospy.logerr(e)

def main():
	# Initialisiere den Knoten
	rospy.init_node(NODE_NAME, anonymous=True)
	try:
		ld_node = LaneDetectorNode(SUB_TOPIC, PUB_TOPIC)
	except KeyboardInterrupt:
		rospy.loginfo("Shutting down node %s", NODE_NAME)

if __name__ == '__main__':
	main()

	
