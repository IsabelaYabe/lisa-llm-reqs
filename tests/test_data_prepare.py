import os
import json
import unittest 
from lisa.sub_lisa.utils import generate_filename_map
from lisa.data_prepare import DataPrepare, RequirementDocumentation, Requirement, Metadata, UserStory, UsageScenario, ReqUsageScenarioMap, UserStoriesUsageScenariosMap, MetadataUsageScenariosMap

class TestDataPrepare(unittest.TestCase):
    
    def setUp(self):
        """
        Set up the test case by initializing the DataPrepare object with mock paths.
        """
        self.mock_dataset = os.path.join("tests", "mocks", "mock_dataset.csv")
        self.mock_req_doc_raw_text = os.path.join("tests", "mocks", "mock_0_req_doc_raw_text")
        self.mock_req_lists = os.path.join("tests", "mocks", "mock_1_req_lists")
        self.mock_doc_struct_metadata = os.path.join("tests", "mocks", "mock_2_doc_struct_metadata")
        self.data_prepare = DataPrepare(
            req_user_stories_dataset=self.mock_dataset, 
            raw_text_doc_dir_path=self.mock_req_doc_raw_text, 
            req_lists_dir_path=self.mock_req_lists, 
            doc_struct_dir_path=self.mock_doc_struct_metadata,
            req_doc_id_keys=generate_filename_map(self.mock_req_doc_raw_text)
                                        )
    def test_get_all_requirement_documentations(self):
        """
        Test the get_all_requirement_documentations method to ensure it correctly retrieves all requirement documentations.
        """
        with open(os.path.join("tests", "mocks", "expecteds", "expected_req_docs.json"), "r") as json_file:
            expected_docs = json.load(json_file)

        all_docs = self.data_prepare._DataPrepare__get_all_requirements_documentations_from_dir()
        self.assertIsInstance(all_docs, list)
        self.assertEqual(len(all_docs), 2)  

        for i, doc in enumerate(all_docs):
            expected = expected_docs[i]
            self.assertIsInstance(doc, RequirementDocumentation)
            self.assertEqual(doc.id, expected["id"])
            self.assertEqual(doc.filename, expected["filename"])
            self.assertEqual(doc.text, expected["text"])    
    
    def test_get_all_metadata(self):
        """
        Test the get_all_metadata method to ensure it correctly retrieves all metadata.
        """
        with open(os.path.join("tests", "mocks", "expecteds", "expected_metadata.json"), "r") as json_file:
            expected_metadata = json.load(json_file)
        
        all_metadata = self.data_prepare._DataPrepare__get_all_metadatas_from_dir()
        self.assertIsInstance(all_metadata, list)
        self.assertEqual(len(all_metadata), 7)  
        
        for i, meta in enumerate(all_metadata):
            expected = expected_metadata[i]
            self.assertIsInstance(meta, Metadata)
            self.assertEqual(meta.id, expected["id"])
            self.assertEqual(meta.doc_name, expected["doc_name"])
            self.assertEqual(meta.text, expected["text"])
            self.assertEqual(meta.req_doc_id, expected["req_doc_id"])
    
    def test_get_all_requirements_from_dir(self):
        """
        Test the get_all_requirements_from_dir method to ensure it correctly retrieves all requirements.
        """
        with open(os.path.join("tests", "mocks", "expecteds", "expected_requirements.json"), "r") as json_file:
            expected_requirements = json.load(json_file)
        
        all_requirements = self.data_prepare._DataPrepare__get_all_requirements_from_dir()
        self.assertIsInstance(all_requirements, list)
        self.assertEqual(len(all_requirements), 9)  
            
        for i, req in enumerate(all_requirements):
            expected = expected_requirements[i]
            self.assertIsInstance(req, Requirement)
            self.assertEqual(req.id, expected["id"])
            self.assertEqual(req.text, expected["text"])
            self.assertEqual(req.metadata_id, expected["metadata_id"])
            self.assertEqual(req.req_doc_id, expected["req_doc_id"])
    
    def test_get_all_user_stories_from_csv(self):
        """
        Test get_all_user_stories_from_csv to ensure it extracts all user stories properly.
        """
        with open(os.path.join("tests", "mocks", "expecteds", "expected_user_stories.json"), "r") as json_file:
            expected_user_stories = json.load(json_file)

        user_stories = self.data_prepare._DataPrepare__get_all_user_stories_from_csv()

        self.assertIsInstance(user_stories, list)
        self.assertEqual(len(user_stories), 47)
        
        for i, user_story in enumerate(user_stories):
            expected = expected_user_stories[i]
            self.assertIsInstance(user_story, UserStory)
            self.assertEqual(user_story.id, expected["id"])
            self.assertEqual(user_story.text, expected["text"])
            self.assertEqual(user_story.metadata_id, expected["metadata_id"])
            self.assertEqual(user_story.req_doc_id, expected["req_doc_id"])            
    
if __name__ == "__main__":
    unittest.main()