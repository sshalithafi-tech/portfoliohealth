import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Custom hook for fetching data with loading and error states
 */
export const useFetch = (url, options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { skip = false, initialData = null } = options;

  const fetchData = useCallback(async () => {
    if (skip) {
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const response = await axios.get(`${BACKEND_URL}${url}`);
      setData(response.data);
      setError(null);
    } catch (err) {
      setError(err);
      setData(initialData);
    } finally {
      setLoading(false);
    }
  }, [url, skip, initialData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
};

/**
 * Custom hook for dashboard data
 */
export const useDashboardData = () => {
  const [stats, setStats] = useState(null);
  const [recentAssessments, setRecentAssessments] = useState([]);
  const [quickAssessments, setQuickAssessments] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [statsRes, assessmentsRes, quickRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/dashboard/stats`),
        axios.get(`${BACKEND_URL}/api/assessments`),
        axios.get(`${BACKEND_URL}/api/quick-assessments`).catch(() => ({ data: [] }))
      ]);
      setStats(statsRes.data);
      setRecentAssessments(assessmentsRes.data.slice(0, 5));
      setQuickAssessments(quickRes.data.slice(0, 3));
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { stats, recentAssessments, quickAssessments, loading, refetch: fetchData };
};

/**
 * Custom hook for companies data
 */
export const useCompanies = () => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchCompanies = useCallback(async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/companies`);
      setCompanies(response.data);
    } catch (err) {
      console.error("Failed to fetch companies:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCompanies();
  }, [fetchCompanies]);

  const addCompany = useCallback((company) => {
    setCompanies(prev => [company, ...prev]);
  }, []);

  return { companies, setCompanies, loading, refetch: fetchCompanies, addCompany };
};

/**
 * Custom hook for assessments data
 */
export const useAssessments = () => {
  const [assessments, setAssessments] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [assessmentsRes, companiesRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/assessments`),
        axios.get(`${BACKEND_URL}/api/companies`)
      ]);
      setAssessments(assessmentsRes.data);
      setCompanies(companiesRes.data);
    } catch (err) {
      console.error("Failed to fetch data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { assessments, companies, loading, refetch: fetchData };
};

/**
 * Custom hook for quick assessment questions
 */
export const useQuickAssessmentQuestions = () => {
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchQuestions = useCallback(async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/quick-assessment/questions`);
      setQuestions(response.data.questions);
    } catch (err) {
      console.error("Failed to fetch questions:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchQuestions();
  }, [fetchQuestions]);

  return { questions, loading };
};

/**
 * Custom hook for assessment details
 */
export const useAssessment = (id) => {
  const [assessment, setAssessment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAssessment = useCallback(async () => {
    if (!id) return;
    try {
      const response = await axios.get(`${BACKEND_URL}/api/assessments/${id}`);
      setAssessment(response.data);
    } catch (err) {
      setError(err);
      console.error("Failed to fetch assessment:", err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchAssessment();
  }, [fetchAssessment]);

  return { assessment, loading, error, refetch: fetchAssessment, setAssessment };
};

/**
 * Custom hook for quick assessment result
 */
export const useQuickAssessmentResult = (id, initialResult = null) => {
  const [result, setResult] = useState(initialResult);
  const [loading, setLoading] = useState(!initialResult);
  const [saved, setSaved] = useState(false);

  const fetchResult = useCallback(async () => {
    if (!id || initialResult) return;
    try {
      const response = await axios.get(`${BACKEND_URL}/api/quick-assessment/${id}`);
      setResult(response.data);
      setSaved(response.data.saved || false);
    } catch (err) {
      console.error("Failed to fetch results:", err);
    } finally {
      setLoading(false);
    }
  }, [id, initialResult]);

  useEffect(() => {
    fetchResult();
  }, [fetchResult]);

  return { result, loading, saved, setSaved };
};
