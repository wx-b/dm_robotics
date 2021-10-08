# Copyright 2020 DeepMind Technologies Limited.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
r"""RGB Objects datasets.

RGB-object datasets are created by applying set of transformations to a cube.

First collection of objects contains 15 objects with assigned colors (red,
green or blue). Naming scheme reflects a color and a group, for example 'r1' is
a red object from group 1. All names are from a set (r, g, b) x (1, 2, 3, 5, 6)
when group 4 is missing from the training set. We also call them
"single-dimensional objects" as they have a single axis of deformation.

Real objects were 3D printed in specific colors following this name convention.
In addition, 5 object triplets have been defined from these objects, each one
containing 1 red, 1 green and 1 blue objects.

Second collection of objects have been generated starting from a seed object
and a set of maximally deformed objects r2, r3, r5, r6, r7, r8. All other
objects are generated by interpolations. 10 objects are inserted linearly
sampling in between the seed and 'rn': dn, fn, en, gn, hn, xn, ln, bn, mn, yn.
Other objects 'Omn' are added with the usual algebra Omn = (Om + On)//2.

A total of 152 objects are in the dataset.

Parameter bounds and specific values used in object creation can be found here
manipulation/props/parametric_object/rgb_objects/parametric_rgb_object.py
"""

import collections
import dataclasses
import enum
import functools
import os
import typing
from typing import Callable, Dict, Iterable, Optional, Sequence, Tuple

from dm_robotics.manipulation.props import mesh_object
from dm_robotics.manipulation.props import object_collection
from dm_robotics.manipulation.props.parametric_object.rgb_objects import parametric_rgb_object
from dm_robotics.manipulation.props.parametric_object.rgb_objects import rgb_object_names
import numpy as np

# Internal resources import.

if typing.TYPE_CHECKING:
  from dm_robotics.manipulation.props.parametric_object import parametric_object

# Workaround for invalid undefined-variable error in PyLint 2.5.
_Singleton = object_collection.Singleton
PropsSetType = object_collection.VersionedSequence


class PropsVersion(enum.Enum):
  """Available types of RGB-objects."""
  RGB_OBJECTS_V1 = parametric_rgb_object.RgbVersion.v1_3


V1 = PropsVersion.RGB_OBJECTS_V1  # short name.


@dataclasses.dataclass
class PropsDatasetType:
  """Class to describe access to a mesh dataset."""
  version: PropsVersion  # RGB-object dataset version.
  ids: Iterable[str]  # List of object names.
  mesh_paths: Iterable[str]  # List of directories to fetch mesh files from.
  scale: float  # Mesh scaling factor.
  # A function to get an object name from a mesh file name.
  get_object_id_func: Callable[[str], str]


_RESOURCES_ROOT_DIR = (
    os.path.join(os.path.dirname(__file__), 'assets'))

## RGB-objects definitions.
_RGB_OBJECTS_MESHES = [
    os.path.join(_RESOURCES_ROOT_DIR, 'rgb_v1/meshes/test_triplets'),
    os.path.join(_RESOURCES_ROOT_DIR, 'rgb_v1/meshes/train'),
    os.path.join(_RESOURCES_ROOT_DIR, 'rgb_v1/meshes/heldout')
]
_RGB_OBJECTS_PARAMS = rgb_object_names.RgbObjectsNames(
    parametric_rgb_object.RgbVersion.v1_3).nicknames
# Objects which name starts with 'd' letter are excluded from the dataset,
# They are sampled too closely in the parametric space to the seed object and
# so have little additional value.
_D_OBJECTS = [x for x in _RGB_OBJECTS_PARAMS if x.startswith('d')]

# s0 is the seed object which is also used in the test triplets.
RGB_OBJECTS_TEST_SET = sorted([
    's0', 'r2', 'r3', 'r5', 'r6', 'b2', 'b3', 'b5', 'b6', 'g2', 'g3', 'g5', 'g6'
])
RGB_OBJECTS_FULL_SET = list((set(_RGB_OBJECTS_PARAMS) - set(_D_OBJECTS)).union(
    set(RGB_OBJECTS_TEST_SET)))

# Held-out set consists of all objects with a single axis of deformation, e.g.
# 't2' etc.
_SINGLE_DEFORMATION_OBJECTS = [x for x in RGB_OBJECTS_FULL_SET if len(x) == 2]
# All single dimension objects are intended for a validataion.
RGB_OBJECTS_HELDOUT_SET = sorted(_SINGLE_DEFORMATION_OBJECTS)
RGB_OBJECTS_TRAIN_SET = list(
    set(RGB_OBJECTS_FULL_SET) - set(RGB_OBJECTS_HELDOUT_SET) -
    set(_D_OBJECTS) - set(RGB_OBJECTS_TEST_SET))
# Arbitrary single letters to use in object naming.
_DEFORMATION_VALUES = ['f', 'e', 'h', 'x', 'l', 'm', 'y', 'r', 'u', 'v']
# 1 and 4 are intentionally excluded.
DEFORMATION_HELDOUT_AXES = ['2', '3', '5', '6']
DEFORMATION_TRAIN_AXES = [
    '23', '25', '26', '35', '36', '37', '38', '56', '57', '58', '67'
]
DEFORMATION_AXES = (DEFORMATION_TRAIN_AXES + DEFORMATION_HELDOUT_AXES)


def _define_deformation_axes() -> Dict[str, Iterable[str]]:
  """Defines object sets for each axis of deformation."""
  rgb_objects_dim = {}
  for a in DEFORMATION_AXES:
    rgb_objects_dim[a] = []
    for v in _DEFORMATION_VALUES:
      obj_id = f'{v}{a}'
      # There are excluded objects we need to check for.
      if obj_id in RGB_OBJECTS_FULL_SET:
        rgb_objects_dim[a].append(f'{v}{a}')
  return rgb_objects_dim


RGB_OBJECTS_DIM = _define_deformation_axes()

# Filename format is <object_id>_<set of parameters>.<mesh file extension>
_RGB_OBJECTS_ID_FROM_FILE_FUNC = lambda filename: filename.split('_')[0]
RGB_OBJECTS_MESH_SCALE = 1.0

PROP_FEATURES = {
    V1:
        PropsDatasetType(
            version=V1,
            ids=RGB_OBJECTS_FULL_SET,
            mesh_paths=_RGB_OBJECTS_MESHES,
            scale=RGB_OBJECTS_MESH_SCALE,
            get_object_id_func=_RGB_OBJECTS_ID_FROM_FILE_FUNC),
}

DEFAULT_COLOR_SET = {
    'RED': [1, 0, 0, 1],
    'GREEN': [0, 1, 0, 1],
    'BLUE': [0, 0, 1, 1]
}


def random_triplet(
    rgb_version: PropsVersion = V1,
    id_list: Optional[Iterable[str]] = None,
    id_list_red: Optional[Iterable[str]] = None,
    id_list_green: Optional[Iterable[str]] = None,
    id_list_blue: Optional[Iterable[str]] = None) -> PropsSetType:
  """Get a triplet of 3 randomly chosen props.

  The function provides a distinct set of 3 prop names. The user can use each
  one of these names to instantinate `RgbObjectProp` object and provide the
  desired color in the constructor.
  For RGB-object dataset v1.0 which contains object names starting with 'R', 'G'
  and 'B' only, the function ensures that exactly one object from each group is
  chosen. For other datasets, the function randomly chooses 3 objects from all
  available in the dataset, without any restrictions.

  Args:
    rgb_version: RGB-Objects version.
    id_list: A list of ids to restrict sampling of objects from.
    id_list_red: A list of ids for the red object. It overrides id_list.
    id_list_green: A list of ids for the green object. It overrides id_list.
    id_list_blue: A list of ids for the blue object. It overrides id_list.

  Returns:
    Random triplet of prop names without replacement.
  """
  if id_list:
    for object_id in id_list:
      if object_id not in PROP_FEATURES[rgb_version].ids:
        raise ValueError(f'id_list includes {object_id} which is not part of '
                         f'{rgb_version}')
  else:
    id_list = PROP_FEATURES[rgb_version].ids
  if not id_list_red:
    id_list_red = id_list
  if not id_list_green:
    id_list_green = id_list
  if not id_list_blue:
    id_list_blue = id_list
  prop_ids = [
      np.random.choice(id_list_red, 1)[0],
      np.random.choice(id_list_green, 1)[0],
      np.random.choice(id_list_blue, 1)[0]
  ]
  return PropsSetType(version=rgb_version, ids=prop_ids)


def fixed_random_triplet(rgb_version: PropsVersion = V1) -> PropsSetType:
  """Gets one of the predefined triplets randomly.

  Args:
    rgb_version: RGB-Objects version. Only v1.0 supported.

  Returns:
    Triplet of object names from a predefined set.
  """
  if rgb_version == V1:
    obj_triplet = np.random.choice(
        [s for s in PROP_TRIPLETS_TEST if s.startswith('rgb_test_triplet')])
    return PROP_TRIPLETS_TEST[obj_triplet]
  else:
    raise ValueError(
        'Sampling predefined tiplets of objects is not implemented for %s' %
        rgb_version.name)


def _define_blue_prop_triplets(
    base_str='rgb_blue_dim',
    id_list=None,
    axes=tuple(DEFORMATION_AXES)) -> Dict[str, functools.partial]:
  """Defines object sets for each axis of deformation."""
  blue_obj_triplets = {}
  for a in axes:
    # Blue objects according to axes of deformation. Red and green are
    # random from the full set.
    blue_obj_triplets[f'{base_str}{a}'] = functools.partial(
        random_triplet,
        rgb_version=V1,
        id_list=id_list,
        id_list_blue=RGB_OBJECTS_DIM[a])
  return blue_obj_triplets


PROP_TRIPLETS_TEST = {
    # Object groups as per 'Triplets v1.0':
    'rgb_test_triplet1': PropsSetType(V1, ('r3', 's0', 'b2')),
    'rgb_test_triplet2': PropsSetType(V1, ('r5', 'g2', 'b3')),
    'rgb_test_triplet3': PropsSetType(V1, ('r6', 'g3', 'b5')),
    'rgb_test_triplet4': PropsSetType(V1, ('s0', 'g5', 'b6')),
    'rgb_test_triplet5': PropsSetType(V1, ('r2', 'g6', 's0')),
}

RANDOM_PROP_TRIPLETS_FUNCTIONS = object_collection.PropSetDict({
    # Return changing triplets on every access.
    'rgb_train_random':
        functools.partial(
            random_triplet, rgb_version=V1, id_list=RGB_OBJECTS_TRAIN_SET),
    'rgb_heldout_random':
        functools.partial(
            random_triplet, rgb_version=V1, id_list=RGB_OBJECTS_HELDOUT_SET),
    'rgb_test_random':   # Randomly loads one of the 5 test triplets.
        functools.partial(fixed_random_triplet, rgb_version=V1),
})

PROP_TRIPLETS = object_collection.PropSetDict({
    **PROP_TRIPLETS_TEST,
    **RANDOM_PROP_TRIPLETS_FUNCTIONS,
})


def _get_all_meshes(rgb_version: PropsVersion = V1) -> Iterable[str]:
  """Get all mesh files from a list of directories."""
  meshes = []
  mesh_paths = PROP_FEATURES[rgb_version].mesh_paths
  for path in mesh_paths:
    for _, _, filenames in os.walk(path):
      meshes.extend(
          os.path.join(path, f)
          for f in filenames
          if f.endswith('.stl'))
  return meshes


class RgbObjectParameters:
  """Parameters and bounds for RGB objects from version 1.0 and above.

  Methods and variables have "generated" in their names to refer to the CAD
  pipeline in which the mesh dataset was originated.
  """

  supported_versions = PropsVersion

  _dataset_generated_params = {}  # contains CAD params for all RGB versions.
  for ver in supported_versions:
    _dataset_generated_params[ver] = rgb_object_names.RgbObjectsNames(
        ver.value).nicknames  # dictionary of CAD params per dataset version.

  @classmethod
  def min_max(
      cls,
      rgb_version) -> Tuple[collections.OrderedDict, collections.OrderedDict]:
    """Calculates min and max values for all dataset parameters."""
    all_params = RgbObjectParameters._dataset_generated_params[rgb_version]
    params_min = next(iter(all_params.values())).copy()  # OrderedDict init.
    params_max = next(iter(all_params.values())).copy()  # OrderedDict init.
    for param_dict in all_params.values():
      for k, v in param_dict.items():
        params_min[k] = min(params_min[k], v)
        params_max[k] = max(params_max[k], v)
    return (params_min, params_max)

  def __init__(self,
               rgb_version: PropsVersion = V1,
               obj_id: Optional[str] = None):
    self._rgb_version = rgb_version
    if rgb_version not in self.supported_versions:
      raise ValueError('Object %s. Version %s not supported. Supported: %s' %
                       (obj_id, rgb_version, self.supported_versions))
    self._generated_params = RgbObjectParameters._dataset_generated_params[
        rgb_version][obj_id]
    self._parametric_object = parametric_rgb_object.RgbObject(rgb_version.value)

  @property
  def rgb_version(self):
    return self._rgb_version

  @property
  def generated_params(self) -> 'parametric_object.ParametersDict':
    """Returns CAD params in {'sds': 4, 'shr': 0, ...} format."""
    return self._generated_params

  @property
  def parametric_object(self) -> 'parametric_object.ParametricObject':
    """Returns parametric_rgb_object.RgbObject with object generation info.

    Example how to validate parameters with parametric_object.ParametricObject
    instance:
      parametric_object = ...  # get instantinated object.
      params = {'sds': 4, 'shr': 0, ...}  # get or create params.
      parametric_object.shape.check_instance(params)  # returns True/False
    """
    return self._parametric_object


class RgbDataset(metaclass=_Singleton):
  """A single instance of a dataset exists per process."""

  def __init__(self):
    self._dataset_stl_paths = {i: None for i in PropsVersion}

  def clear_cache(self):
    self._dataset_stl_paths = {i: None for i in PropsVersion}

  def __call__(self, rgb_version: PropsVersion = V1):
    if not self._dataset_stl_paths[rgb_version]:
      self._dataset_stl_paths[rgb_version] = _get_all_meshes(rgb_version)
    return self._dataset_stl_paths[rgb_version]


class RgbObjectProp(mesh_object.MeshProp):
  """RGB-Object from meshes."""

  def _build(self,
             rgb_version: PropsVersion = V1,
             obj_id: Optional[str] = None,
             name: str = 'rgb_object',
             size: Optional[Sequence[float]] = None,
             color: Optional[str] = None,
             pos: Optional[Sequence[float]] = None,
             randomize_size: bool = False,
             mjcf_model_export_dir: Optional[str] = None):
    stl_paths = RgbDataset()(rgb_version)
    if size is None:
      size = [PROP_FEATURES[rgb_version].scale] * 3
    if randomize_size:
      # Size of the prop is randomly scaled by [0.8, 1.1]
      # of the initial value. Size randomization encourages a more conservative
      # agent behaviour.
      size = np.array(size)
      size *= np.random.random() * .3 + .8
      size = list(size)
    for path in stl_paths:
      object_id_from_file = PROP_FEATURES[rgb_version].get_object_id_func(
          os.path.basename(path))
      if obj_id == object_id_from_file:
        if rgb_version in RgbObjectParameters.supported_versions:
          self._object_params = RgbObjectParameters(rgb_version, obj_id)
        else:
          self._object_params = None
        return super()._build(
            visual_meshes=[path],
            name=name,
            size=size,
            color=color,
            pos=pos,
            mjcf_model_export_dir=mjcf_model_export_dir)

    raise ValueError('Object ID %s does not exist in directories %s' %
                     (obj_id, PROP_FEATURES[rgb_version].mesh_paths))

  @property
  def object_params(self) -> Optional[RgbObjectParameters]:
    """None for unsupported versions."""
    return self._object_params


class RandomRgbObjectProp(mesh_object.MeshProp):
  """Uniformly sample one object mesh from a mesh directory.

  Currently, the picked random object could belong to any of train/test sets.
  The planned open source version will provide random objects from the train set
  only.
  """

  def _build(self,
             rgb_version: PropsVersion = V1,
             name: str = 'rgb_object',
             size: Optional[Sequence[float]] = None,
             color: Optional[str] = None,
             pos: Optional[Sequence[float]] = None,
             mjcf_model_export_dir: Optional[str] = None):
    mesh_dataset = RgbDataset()
    stl_path = np.random.choice(mesh_dataset(rgb_version))
    if size is None:
      size = [PROP_FEATURES[rgb_version].scale] * 3
    object_id_from_file = PROP_FEATURES[rgb_version].get_object_id_func(
        os.path.basename(stl_path))
    if rgb_version in RgbObjectParameters.supported_versions:
      self._object_params = RgbObjectParameters(rgb_version,
                                                object_id_from_file)
    else:
      self._object_params = None
    return super()._build(
        visual_meshes=[stl_path],
        name=name,
        size=size,
        color=color,
        pos=pos,
        mjcf_model_export_dir=mjcf_model_export_dir)

  @property
  def object_params(self) -> Optional[RgbObjectParameters]:
    """None for unsupported versions."""
    return self._object_params
