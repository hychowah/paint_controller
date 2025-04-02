import os.path
import json

from PySide6.QtCore import QObject, Signal, Property, Slot

from towngas_interfaces.msg import WinchStatus, WheelStatus, SteamDeckInput, TeensyStatus, TeensyYaw, MoveWinchLength, MoveWheelSpeeds

class TrajectoryHandler(QObject):

    trajectoryChanged = Signal()
    #actionChanged = Signal()

    def __init__(self, winch_cmd_pub=None):
        super().__init__()
        self._trajectory = []
        self._currentTrajDescription = []
        self._currentTrajCmd = []
        #self._currentActionInx = 0

        self.winch_cmd_pub = winch_cmd_pub

        self.filePath = os.path.join(os.path.dirname(__file__), 'resource', 'trajectory.json')

        self.readTrajectoryFromJSONFile()

    def readTrajectoryFromJSONFile(self):
        # check if file exists
        # if not, create it
        # if it does, read it
        if os.path.exists(self.filePath):
            with open(self.filePath, 'r') as file:
                self._trajectory = json.load(file)
        else:
            self._trajectory = []
            self._saveTrajectory()

        self.trajectoryChanged.emit()

    def _saveTrajectory(self):
        """Internal method to save data"""
        with open(self.filePath, 'w') as file:
            json.dump(self._trajectory, file, indent=2)

    def pubWinchCmd(self, cmd):
        msg = MoveWinchLength()
        msg.length_mm = int(cmd[1])
        msg.speed_mm_s = int(cmd[2])
        self.winch_cmd_pub.publish(msg)

    @Property(list, notify=trajectoryChanged)
    def trajectory(self):
        return self._trajectory

    
    @Slot(int)
    def deleteTrajectory(self, index):
        if 0 <= index < len(self._trajectory):
            del self._trajectory[index]
            self._saveTrajectory()
            self.trajectoryChanged.emit()

    @Slot(str, str)
    def saveTrajectory(self, name, sequence):
        added = True
        for item in self._trajectory:
            if item["name"] == name:
                item["sequence"] = sequence
                added = False
                break
        if added:
            self._trajectory.append({"name": name, "sequence": sequence})

        self._saveTrajectory()
        self.trajectoryChanged.emit()

    @Slot(int)
    def selectTrajectory(self, index):
        if 0 <= index < len(self._trajectory):
            # reset current trajectory
            self._currentTrajCmd = []
            self._currentTrajDescription = []

            trajStr = self._trajectory[index]["sequence"]
            actions = trajStr.split(',')
            for action in actions:
                temp = action.split('_')
                if temp[0] == 'ascent':
                    self._currentTrajDescription.append("Ascent " + temp[1] + "mm with \n speed " + temp[2] + "mm/s")
                    self._currentTrajCmd.append(["winch", temp[1], temp[2]])
                elif temp[0] == 'descent':
                    self._currentTrajDescription.append("Descent " + temp[1] + "mm with \n speed " + temp[2] + "mm/s")
                    self._currentTrajCmd.append(["winch", "-"+temp[1], temp[2]])
                elif temp[0] == 'spray':
                    self._currentTrajDescription.append("Move gun to " + temp[1] + "mm")
                    self._currentTrajCmd.append(["moveGun", temp[1]])
                    self._currentTrajDescription.append("Spray with speed " + temp[2] + "mm/s")
                    self._currentTrajCmd.append(["spray", temp[2]])
                elif temp[0] == 'stopSpray':
                    self._currentTrajDescription.append("Stop spraying")
                    self._currentTrajCmd.append(["moveGun", "0"])
                    self._currentTrajDescription.append("Retract gun")
                    self._currentTrajCmd.append(["spray", "0"])
                elif temp[0] == "aNs":
                    self._currentTrajDescription.append("Move gun to " + temp[3] + "mm")
                    self._currentTrajCmd.append(["moveGun", temp[3]])
                    self._currentTrajDescription.append("Ascent " + temp[1] + "mm with \n speed " + temp[2] + "mm/s \n and spray with speed " + temp[4] + "mm/s")
                    self._currentTrajCmd.append(["winchNspray", temp[1], temp[2], temp[4]])
                elif temp[0] == "dNs":
                    self._currentTrajDescription.append("Move gun to " + temp[3] + "mm")
                    self._currentTrajCmd.append(["moveGun", temp[3]])
                    self._currentTrajDescription.append("Descent " + temp[1] + "mm with \n speed " + temp[2] + "mm/s \n and spray with speed " + temp[4] + "mm/s")
                    self._currentTrajCmd.append(["winchNspray", "-"+temp[1], temp[2], temp[4]])
                elif temp[0] == "resetYaw":
                    self._currentTrajDescription.append("Reset yaw")
                    self._currentTrajCmd.append(["resetYaw"])

    @Slot(result=list)
    def getSelectedActions(self):
        return self._currentTrajDescription
    
    @Slot(int)
    def startExecution(self, index):
        if 0 <= index < len(self._currentTrajCmd):
            if self._currentTrajCmd[index][0] == "winch":
                self.pubWinchCmd(self._currentTrajCmd[index])
            elif self._currentTrajCmd[index][0] == "moveGun":
                pass # TODO
            elif self._currentTrajCmd[index][0] == "spray":
                pass # TODO
            elif self._currentTrajCmd[index][0] == "winchNspray":
                pass # TODO
            elif self._currentTrajCmd[index][0] == "resetYaw":
                pass # TODO

    @Slot()
    def stopAll(self):
        pass # TODO
