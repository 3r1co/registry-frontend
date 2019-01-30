import { shallow } from 'enzyme';
import React  from 'react';

import RepositoryTable from './RepositoryTable';

describe('RepositoryTable', () => {
  it('fetches data from server when server returns a successful response', done => {
    const mockSuccessResponse = {data: [{repo: "alpine", size: "1000", tags:["latest"]}]};
    const mockJsonPromise = Promise.resolve(mockSuccessResponse);
    const mockFetchPromise = Promise.resolve({
      json: () => mockJsonPromise,
    });
    jest.spyOn(global, 'fetch').mockImplementation(() => mockFetchPromise);
    
    const table = shallow(<RepositoryTable />);
                            
    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(global.fetch).toHaveBeenCalledWith('/api/repositories');

    process.nextTick(() => {
      expect(table.state()).toEqual({
        "error": null,
        "isLoaded": true,
        "items": [{repo: "alpine", size: "1000", tags:["latest"]}]
      });

      global.fetch.mockClear();
      done();
    });
  });
});