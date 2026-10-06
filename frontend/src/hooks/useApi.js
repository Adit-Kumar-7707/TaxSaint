// TaxSaint API request hook

import { useState, useCallback } from "react";


// reusable API hook
function useApi(apiFunction) {

  // response data
  const [data, setData] = useState(null);

  // request loading state
  const [loading, setLoading] = useState(false);

  // request error
  const [error, setError] = useState(null);


  // execute API request
  const execute = useCallback(async (...args) => {

    // clear previous error
    setError(null);

    // mark request as active
    setLoading(true);

    try {

      // validate API function
      if (typeof apiFunction !== "function") {
        throw new Error("API function is required.");
      }

      // execute API function
      const response = await apiFunction(...args);

      // store successful response
      setData(response);

      // return response to caller
      return response;

    } catch (requestError) {

      // convert unknown errors into Error objects
      const normalizedError =
        requestError instanceof Error
          ? requestError
          : new Error("API request failed.");

      // store request error
      setError(normalizedError);

      // return error to caller
      throw normalizedError;

    } finally {

      // mark request as completed
      setLoading(false);
    }

  }, [apiFunction]);


  // reset request state
  const reset = useCallback(() => {

    // clear response data
    setData(null);

    // clear request error
    setError(null);

    // reset loading state
    setLoading(false);

  }, []);


  // hook interface
  return {
    data,
    loading,
    error,
    execute,
    reset
  };
}


// export API hook
export default useApi;