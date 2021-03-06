#!/usr/bin/env python

# ROS node for the Neato Robot Vacuum
# Copyright (c) 2010 University at Albany. All right reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the University at Albany nor the names of its 
#       contributors may be used to endorse or promote products derived 
#       from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL VANADIUM LABS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
ROS node for Neato XV-11 Robot Vacuum.
"""

__author__ = "ferguson@cs.albany.edu (Michael Ferguson)"

import roslib; roslib.load_manifest("neato_node1")
import rospy
from math import sin,cos, atan, degrees
from Tkinter import *
from evidencegrid import EvidenceGrid
import window
import ImageTK
import numpy as np

import ransac
import EKF
import data_association
#import threading

from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Quaternion
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from tf.broadcaster import TransformBroadcaster

from neato_driver.neato_driver import xv11, BASE_WIDTH, MAX_SPEED

class NeatoNode:

    def __init__(self):
        """ Start up connection to the Neato Robot. """
        rospy.init_node('neato1')

        self.port = rospy.get_param('~port', "/dev/ttyACM0")
        rospy.loginfo("Using port: %s"%(self.port))

        self.robot = xv11(self.port)

        rospy.Subscriber("cmd_vel", Twist, self.cmdVelCb)
        self.scanPub = rospy.Publisher('base_scan', LaserScan, queue_size=10)
        self.odomPub = rospy.Publisher('odom', Odometry, queue_size=10)
        self.odomBroadcaster = TransformBroadcaster()

        self.cmd_vel = [10,10] 

    def main(self):        
        encoders = [0,0]

        self.x = 0     # position in xy plane
        self.y = 0
        self.th = 0
		self.landmarks = []
        then = rospy.Time.now()

        # things that don't ever change
        scan_link = rospy.get_param('~frame_id','base_laser_link')
        scan = LaserScan(header=rospy.Header(frame_id=scan_link)) 
        scan.angle_min = 0
        scan.angle_max = 6.26
        scan.angle_increment = 0.017437326
        scan.range_min = 0.020
        scan.range_max = 5.0
        odom = Odometry(header=rospy.Header(frame_id="odom"), child_frame_id='base_link')
		goal = [5,5] # [x,y]
		alpha = .10
		thalpha = .05
		subgoal = goal
		#X = [0.0, 0.0, 0.0] #X matrix for EKF - starts out at pose 0,0,0 w/ no landmarks.
		check = True #toggle
    
        # main loop of driver
        r = rospy.Rate(2)
        while not rospy.is_shutdown():
		
			# get motor encoder values
			left, right = self.robot.getMotors()
			
            if(check): 
				self.robot.requestScan()
				# prepare laser scan
            	scan.header.stamp = rospy.Time.now()    
            	#self.robot.requestScan()
            	scan.ranges = self.robot.getScanRanges()

				# send updated movement commands
				# We're using Tangent Bug here.
				# Finding angle to turn to in order to reach the goal 
				distToGoal = sqrt((goal[0] - this.x) ** 2 + (goal[1] - this.y) ** 2)
				thetaToGoal = Math.sin(goal[1]/goal[0]) - Math.sin(this.y/this.x) #w/ respect to x axis. 
				
				# getting the point that minimizes the distance from point to goal
				minGoalDist = min(scan.ranges, key = lambda d: sqrt((goal[0] - (this.x + math.cos(scan.ranges.index(d) / d))) ** 2 + (goal[1] - (this.y + math.sin(scan.ranges.index(d) / d))) ** 2)) 
				minGoalDistAngle = scan.ranges.index(minGoalDist)
				
				# now we want to go to that location for as long as we can.....
				subgoal = [this.x + math.cos(minGoalDistAngle / minGoalDist), this.y + math.sin(minGoalDistAngle / minGoalDist)]
				
				#checking to see if we're done
				if(abs(this.th - minGoalDistAngle) <= thalpha): 
					if((abs(subgoal[0] - this.x) <= alpha) and (abs(subgoal[1] - this.y) <= alpha):
						self.cmd_vel = [0,0]; # we're at the subgoal/goal. Just chill for a sec (+/- alpha)
					else: # we're at the right angle, but wrong location.
						self.cmd_vel[100, 100]
				else: #wrong angle
					self.cmd_vel = [30, 0]

				self.robot.setMotors(self.cmd_vel[0], self.cmd_vel[1], max(abs(self.cmd_vel[0]),abs(self.cmd_vel[1])))
            
            # ask for the next scan while we finish processing stuff
            # Don't think I want two scans right now, commenting out
			# self.robot.requestScan()
			
			#send the old values to the evidence grid
			for i in range (0, len(ranges)):
				if(ranges[i] >= 0.020): 
					self.grid.observe_something(ranges[i], (i * 0.017437326), self.x, self.y)
				else
					self.grid.observe_nothing((i * 0.017437326), self.x, self.y)
            
            # now update position information
            dt = (scan.header.stamp - then).to_sec()
            then = scan.header.stamp

            d_left = (left - encoders[0])/1000.0
            d_right = (right - encoders[1])/1000.0
            encoders = [left, right]
            
            dx = (d_left+d_right)/2
            dth = (d_right-d_left)/(BASE_WIDTH/1000.0)
			
			x = cos(dth)*dx
            y = -sin(dth)*dx
            self.x += cos(self.th)*x - sin(self.th)*y
            self.y += sin(self.th)*x + cos(self.th)*y
            self.th += dth
			
			#distance travelled. 
			
			'''
			Start EKF
			'''
			update_from_odom(self.x, self.y, self.th)
			extracted = ransac_go(scan.ranges)
			
			#new_set[0] = old landmarks, [1] = new landmarks
			new_set = data_association(extracted, landmarks)
			update_from_reobserved(new_set[0])
			landmarks = add_new_landmarks(landmarks[1])
			

            # prepare tf from base_link to odom
            quaternion = Quaternion()
            quaternion.z = sin(self.th/2.0)
            quaternion.w = cos(self.th/2.0)

            # prepare odometry
            odom.header.stamp = rospy.Time.now()
            odom.pose.pose.position.x = self.x
            odom.pose.pose.position.y = self.y
            odom.pose.pose.position.z = 0
            odom.pose.pose.orientation = quaternion
            odom.twist.twist.linear.x = dx/dt
            odom.twist.twist.angular.z = dth/dt

            # publish everything
            self.odomBroadcaster.sendTransform( (self.x, self.y, 0), (quaternion.x, quaternion.y, quaternion.z, quaternion.w),
                then, "base_link", "odom" )
            self.scanPub.publish(scan)
            self.odomPub.publish(odom)

            # wait, then do it again
            r.sleep()

        # shut down
        self.robot.setLDS("off")
        self.robot.setTestMode("off") 

    def cmdVelCb(self,req):
        x = req.linear.x * 1000
        th = req.angular.z * (BASE_WIDTH/2) 
        k = max(abs(x-th),abs(x+th))
        # sending commands higher than max speed will fail
        if k > MAX_SPEED:
            x = x*MAX_SPEED/k; th = th*MAX_SPEED/k
        self.cmd_vel = [ int(x-th) , int(x+th) ]

if __name__ == "__main__":    
    try: 
		robot = NeatoNode()
		self.grid = EvidenceGrid(0.01, 512, 512) #evidence grid
		self.efk = EFK()
		robot.main()
	except rospy.ROSInterruptException: 
		pass
