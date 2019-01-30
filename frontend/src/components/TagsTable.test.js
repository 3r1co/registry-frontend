import { shallow } from 'enzyme';
import React  from 'react';

import TagsTable from './TagsTable';

describe('TagsTable', () => {
  it('fetches data from server when server returns a successful response', done => {
    const mockSuccessResponse = {tags: [{ repo: "alpine", tag: "latest", sizes: { "layer1": 1, "layer2": 2 } } ] };
    const mockJsonPromise = Promise.resolve(mockSuccessResponse);
    const mockFetchPromise = Promise.resolve({
      json: () => mockJsonPromise,
    });
    jest.spyOn(global, 'fetch').mockImplementation(() => mockFetchPromise);
    
    const table = shallow(<TagsTable />);
                            
    expect(global.fetch).toHaveBeenCalledTimes(0);

    table.instance().setRepo("alpine")

    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(global.fetch).toHaveBeenCalledWith('/api/tags/alpine');

    process.nextTick(() => {
      expect(table.state()).toEqual({
        "error": null,
        "isLoaded": true,
        "items": [{ repo: "alpine", tag: "latest", sizes: { "layer1": 1, "layer2": 2 } } ]
      });

      global.fetch.mockClear();
      done();
    });
  });
});