import numpy as np
from Analysis.image import Image

from BoundingBoxes import BoundingBoxes
from Evaluator import *

class DatasetType(Enum):
    EIPH_Exact = 1
    MitoticFigure = 2
    Asthma = 3
    EIPH_LabelBox = 4

    def __str__(self):
        return self.name

class ProjectType(Enum):
    Annotation = 1
    ExpertAlgorithm = 2
    GroundTruth = 3
    
    def __str__(self):
        return self.name

class Expert:

    def __init__(self, participant, bbType, dataset_type: DatasetType, annotation_type: ProjectType):

        self.participant = participant 
        self.images = {}
        self.bbType = bbType
        self.dataset_type = dataset_type
        self.annotation_type = annotation_type

    @property
    def Images(self):
        return self.images

    @property
    def ProjectType(self):
        return self.annotation_type

    @property
    def DatasetType(self):
        return self.dataset_type

    @property
    def expert(self):
        return self.participant 

    @property
    def total_annotations(self):
        return sum([len(image.Labels) for image in self.images.values()])

    @property
    def annotations_per_image(self):
        return {image.FileName: len(image.Labels) for image in self.images.values()}

    @property
    def total_seconds_to_label(self):
        return sum([image.seconds_to_label for image in self.images.values() if image.seconds_to_label is not None])

    @property
    def mean_seconds_to_label(self):
        return np.array([image.seconds_to_label for image in self.images.values() if image.seconds_to_label is not None]).mean()

    def calc_metrics(self, second_expert, iou_thresh: float=0.25):

        boundingBoxes = BoundingBoxes()

        for image in self.images.values():
            for bb in image.BB_Boxes:
                boundingBoxes.addBoundingBox(bb)

        for image in second_expert.images.values():
            for bb in image.BB_Boxes:
                boundingBoxes.addBoundingBox(bb)

        evaluator = Evaluator()
        metricsPerClass = evaluator.GetPascalVOCMetrics(boundingBoxes, iou_thresh)

        return metricsPerClass


    def calc_MIoU(self, second_expert, iou_thresh: float=0.25):

        metricsPerClass = self.calc_metrics(second_expert, iou_thresh)

        return np.mean([np.nan_to_num(mc['AP']) for mc in metricsPerClass])

    def calc_sensitivity(self, second_expert, iou_thresh: float=0.25):

        metricsPerClass = self.calc_metrics(second_expert, iou_thresh)

        sensitivity = []
        for mc in metricsPerClass:
            tp = mc['total TP']
            fn = mc['total positives'] -  mc['total TP']

            sensitivity.append(tp / (tp + fn))

        return np.mean(sensitivity)

    def calc_specificity(self, second_expert, fake_cells, iou_thresh: float=0.25):

        metricsPerClass = self.calc_metrics(second_expert, iou_thresh)
        metricsPerClassFakeCells = self.calc_metrics(fake_cells, iou_thresh)

        specificity = []
        for mc, fake in zip(metricsPerClass, metricsPerClassFakeCells):
            fp = mc['total FP']
            tn = fake['total positives'] - fake['total TP']

            specificity.append(tn / (tn + fp))

        return np.mean(specificity)


    def add_file(self, path : str):

        listOfLines = []

        with open(path, "r") as fileHandler:
            # Get list of all lines in file
            listOfLines = fileHandler.readlines()

        for line in listOfLines:
            splits = line.replace('[','').replace(']','').split('|')

            if len(splits) < 3:
                continue
            
            file_name = splits[0]
            if file_name not in self.images:
                self.images[file_name] = Image(file_name, self.participant, self.bbType)

            self.images[file_name].add_line_information(line)

    def __repr__(self):
        return "{0}:  Annos: {1} Seconds: {2} Type: {3} Project: {4}".format(self.expert, self.total_annotations, self.mean_seconds_to_label, self.dataset_type, self.annotation_type)

