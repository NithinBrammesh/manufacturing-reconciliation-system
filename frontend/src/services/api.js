  const BASE_URL = "/api";  

  export const getAllMetrics = async () => {
    const response = await fetch(`${BASE_URL}/reconciliation`);

    if (!response.ok) {
      throw new Error("Failed to fetch reconciliation data");
    }

    return response.json();
  };

  export const getLines = async () => {
    const response = await fetch(`${BASE_URL}/lines`);

    if (!response.ok) {
      throw new Error("Failed to fetch production lines");
    }

    return response.json();
  };