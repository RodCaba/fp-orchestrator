from abc import ABC, abstractmethod


class BaseStorage(ABC):
    """
    Abstract base class for storage systems.
    """

    @abstractmethod
    def save(self, data):
        """
        Save data to the storage system.
        
        :param data: Data to be saved.
        """
        pass

    @abstractmethod
    def load(self, identifier):
        """
        Load data from the storage system using an identifier.
        
        :param identifier: Unique identifier for the data.
        :return: Loaded data.
        """
        pass

    @abstractmethod
    def download(self, identifier, file_path):
        """
        Download data from the storage system using an identifier.
        
        :param identifier: Unique identifier for the data.
        :param file_path: Local file path to save the downloaded data.
        :return: Path to the downloaded file.
        """
        pass

    @abstractmethod
    def list_objects(self, prefix: str = ''):
        """
        List objects in the storage system from a directory.
        
        :param prefix: Prefix directory to filter the objects.
        :return: List of object identifiers.
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if the storage system is connected.
        
        :return: True if connected, False otherwise.
        """
        pass