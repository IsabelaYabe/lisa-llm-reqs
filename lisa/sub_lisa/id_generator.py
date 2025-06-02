import os
from dataclasses import dataclass
from typing import Dict, Any
from abc import ABC, abstractmethod

@dataclass(frozen=True, slots=True)
class ID(ABC):
    id: Any
    
    @classmethod
    @abstractmethod
    def from_str(cls, id_str: str) -> "ID":
        """Convert a string to an ID object."""
        raise NotImplementedError("Subclasses should implement this method.")
    
@dataclass(frozen=True, slots=True)
class ModelGeneratorID(ID):
    id: int

    def __str__(self):
        return str(self.id)
    
    def __repr__(self):
        return f"ModelGeneratorID(id={self.id})"
    
    def __eq__(self, other):
        return isinstance(other, ModelGeneratorID) and self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
    
    @classmethod
    def from_str(cls, id_str: str) -> "ModelGeneratorID":
        try:
            id_int = int(id_str)
            return cls(id=id_int)
        except ValueError:
            raise ValueError(f"Invalid ID string: {id_str}. Expected an integer.")

@dataclass(frozen=True, slots=True)
class ClusterID:
    id: int

    def __str__(self):
        return str(self.id)
    
    def __repr__(self):
        return f"ClusterID(id={self.id})"
    
    def __eq__(self, other):
        return isinstance(other, ClusterID) and self.id == other.id
    
    def __hash__(self):
        return hash(self.id)

    @classmethod
    def from_str(cls, id_str: str) -> "ClusterID":
        try:
            id_int = int(id_str)
            return cls(id=id_int)
        except ValueError:
            raise ValueError(f"Invalid ID string: {id_str}. Expected an integer.")
    
@dataclass(frozen=True, slots=True)
class RequirementDocumentationID:
    id: int
    
    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return f"RequirementDocumentationID(id={self.id})"

    def __eq__(self, other):
        return isinstance(other, RequirementDocumentationID) and self.id == other.id

    def __hash__(self):
        return hash(self.id)
    
    @classmethod
    def from_str(cls, id_str: str) -> "RequirementDocumentationID":
        try:
            id_int = int(id_str)
            return cls(id=id_int)
        except ValueError:
            raise ValueError(f"Invalid ID string: {id_str}. Expected an integer.")
    
@dataclass(frozen=True, slots=True)
class SectionID:
    requirement_documentation_key: RequirementDocumentationID
    id: str
    
    def __str__(self):
        return f"{self.requirement_documentation_key}-{self.id}"

    def __repr__(self):
        return f"SectionID(requirement_documentation_key={self.requirement_documentation_key}, id={self.id})"
    
    def __eq__(self, other):
        return isinstance(other, SectionID) and self.requirement_documentation_key == other.requirement_documentation_key and self.id == other.id

    def __hash__(self):
        return hash((self.requirement_documentation_key, self.id))
    
    @classmethod
    def from_str(cls, id_str: str) -> "SectionID":
        try:
            requirement_documentation_key_str, id = id_str.split('-')
            requirement_documentation_key = RequirementDocumentationID.from_str(requirement_documentation_key_str)
            
            return cls(requirement_documentation_key=requirement_documentation_key, id=id)
        except ValueError:
            raise ValueError(f"Invalid ID string: {id_str}. Expected format: <RequirementDocumentationID>-<id>.")    
    
@dataclass(frozen=True, slots=True)        
class RequirementID:
    requirement_documentation_key: RequirementDocumentationID
    section_key: str
    id: int

    def __str__(self):
        return f"{self.requirement_documentation_key}-{self.section_key}-{self.id}"

    def __repr__(self):
        return f"RequirementID(requirement_documentation_key={self.requirement_documentation_key}, section_key={self.section_key}, id={self.id})"

    def __eq__(self, other):
        return isinstance(other, RequirementID) and self.requirement_documentation_key == other.requirement_documentation_key and self.section_key == other.section_key and self.id == other.id

    def __hash__(self):
        return hash((self.requirement_documentation_key, self.section_key, self.id))
    
    @classmethod
    def from_str(cls, id_str: str) -> "RequirementID":
        try:
            head, id_part = id_str.rsplit('-', 1)
            requirement_documentation_key_str, section_key = head.split('-', 1)
            requirement_documentation_key = RequirementDocumentationID.from_str(requirement_documentation_key_str)
            id = int(id_part)
            return cls(requirement_documentation_key=requirement_documentation_key, section_key=section_key, id=id)
        except ValueError:
            raise ValueError(f"Invalid ID string: {id_str}. Expected format: <RequirementDocumentationID>-<section_key>-<id>.")
    

@dataclass(frozen=True, slots=True)    
class UserStoryID:
    requirement_id: RequirementID
    model_generator_id: ModelGeneratorID
    id: int
    
    def __str__(self):
        return f"{self.requirement_id}-{self.model_generator_id}.{self.id}"
    
    def __repr__(self):
        return f"UserStoryID(requirement_id={self.requirement_id}, model_generator_id={self.model_generator_id}, id={self.id})"
    
    def __eq__(self, other):
        return isinstance(other, UserStoryID) and self.requirement_id == other.requirement_id and self.model_generator_id == other.model_generator_id and self.id == other.id
    
    def __hash__(self):
        return hash((self.requirement_id, self.model_generator_id, self.id))
    
    @classmethod
    def from_str(cls, id_str: str) -> "UserStoryID":
        try:
            req_part, id = id_str.rsplit('.', 1)  
            requirement_id_str, model_generator_id_str = req_part.rsplit('-', 1)
            requirement_id = RequirementID.from_str(requirement_id_str)
            model_generator_id = ModelGeneratorID.from_str(model_generator_id_str)
            id = int(id)
            return cls(requirement_id=requirement_id, model_generator_id=model_generator_id, id=id)
        except ValueError:
            raise ValueError(f"Invalid ID string: {id_str}. Expected format: <RequirementID>-<ModelGeneratorID>.<id>")

        
@dataclass(frozen=True, slots=True)
class UsageScenarioID:
    requirement_documentation_key: RequirementDocumentationID
    cluster_id: ClusterID
    model_generator_key: ModelGeneratorID
    id: int

    def __str__(self):
        return f"{self.requirement_documentation_key}-{self.cluster_id}-{self.model_generator_key}.{self.id}"
    
    def __repr__(self):
        return f"UsageScenarioID(requirement_documentation_key={self.requirement_documentation_key}, cluster_id={self.cluster_id}, model_generator_key={self.model_generator_key}, id={self.id})"
    
    def __eq__(self, other):
        return isinstance(other, UsageScenarioID) and self.requirement_documentation_key == other.requirement_documentation_key and self.cluster_id == other.cluster_id and self.model_generator_key == other.model_generator_key and self.id == other.id
    
    def __hash__(self):
        return hash((self.requirement_documentation_key, self.cluster_id, self.model_generator_key, self.id))
    
    @classmethod
    def from_str(cls, id_str: str) -> "UsageScenarioID":
        try:
            complement, id = id_str.rsplit('.', 1)
            requirement_documentation_key_str, cluster_id_str, model_generator_id_str = complement.split('-')
            requirement_documentation_key = RequirementDocumentationID.from_str(requirement_documentation_key_str)
            cluster_id = ClusterID(cluster_id_str)
            model_generator_key = ModelGeneratorID.from_str(model_generator_id_str)
            id = int(id)
            return cls(
                requirement_documentation_key=requirement_documentation_key,
                cluster_id=cluster_id,
                model_generator_key=model_generator_key,
                id=id
            )
        except ValueError:
            raise ValueError(f"Invalid ID string: {id_str}. Expected format: <RequirementDocumentationID>-<ClusterID>-<ModelGeneratorID>.<id>")


class IDGenerator:
    def __init__(self, requirement_docs_folder_path: str):
        self._filenames_map = None 
        self._requirement_docs_id = None
        self.__map = self.__generate_filename_map(requirement_docs_folder_path)
        
    def __generate_filename_map(self, directory):
        filenames_map = {}
        map_filenames = {}

        files = sorted(os.listdir(directory))
        for i, file in enumerate(files):
            filename = os.path.splitext(file)[0]
            requirement_documentation_id= RequirementDocumentationID(id=i)
            filenames_map[filename] = requirement_documentation_id
            map_filenames[requirement_documentation_id] = filename

        return filenames_map, map_filenames 
    
    def generate_requirement_documentation_id(self, filename: str) -> RequirementDocumentationID:
        return self.filenames_map[filename]
    
    def generate_section_id(self, filename: str, section_key: str) -> SectionID:
        requirement_documentation_key = self.generate_requirement_documentation_id(filename)
        return SectionID(requirement_documentation_key=requirement_documentation_key, id=section_key)
    
    def generate_requirement_id(self, section_id: SectionID, requirement_key: int) -> RequirementID:
        requirement_documentation_key = section_id.requirement_documentation_key
        section_key = section_id.id
        return RequirementID(requirement_documentation_key=requirement_documentation_key, section_key=section_key, id=requirement_key)
    
    def generate_user_story_id(self, requirement_id: RequirementID, model_generator_id: ModelGeneratorID, id: int) -> UserStoryID:
        return UserStoryID(requirement_id=requirement_id, model_generator_id=model_generator_id, id=id)
    
    def generate_usage_scenario_id(self, filename: str, cluster_id: ClusterID, model_generator_id: ModelGeneratorID, usage_scenario_key: int) -> UsageScenarioID:
        requirement_documentation_key = self.generate_requirement_documentation_id(filename)
        return UsageScenarioID(
            requirement_documentation_key=requirement_documentation_key,
            cluster_id=cluster_id,
            model_generator_key=model_generator_id,
            id=usage_scenario_key
        )


    @property
    def filenames_map(self) -> Dict[str, RequirementDocumentationID]:
        if self._filenames_map is None:
            self._filenames_map = self.__map[0]
        return self._filenames_map
    
    @property
    def requirement_docs_id(self) -> Dict[RequirementDocumentationID, str]:
        if self._requirement_docs_id is None:
            self._requirement_docs_id = self.__map[1]
        return self._requirement_docs_id