import React, { useState, useEffect } from 'react';
import { useTable } from 'react-table';
import axios from 'axios';

const SymbolTable = () => {
    const [symbols, setSymbols] = useState([]);

    useEffect(() => {
        axios.get('/api/symbols')
            .then(response => {
                setSymbols(response.data);
            });
    }, []);

    const columns = React.useMemo(
        () => [
            {
                Header: 'Symbol',
                accessor: 'symbol',
            },
            {
                Header: 'Profit/Loss',
                accessor: 'profitLoss',
            },
        ],
        []
    );

    const {
        getTableProps,
        getTableBodyProps,
        headerGroups,
        rows,
        prepareRow,
    } = useTable({ columns, data: symbols });

    return (
        <div>
            <h2>Symbol Table</h2>
            <table {...getTableProps()} style={{ border: 'solid 1px black' }}>
                <thead>
                    {headerGroups.map(headerGroup => (
                        <tr {...headerGroup.getHeaderGroupProps()}>
                            {headerGroup.headers.map(column => (
                                <th
                                    {...column.getHeaderProps()}
                                    style={{
                                        borderBottom: 'solid 3px black',
                                        background: 'aliceblue',
                                        color: 'black',
                                        fontWeight: 'bold',
                                    }}
                                >
                                    {column.render('Header')}
                                </th>
                            ))}
                        </tr>
                    ))}
                </thead>
                <tbody {...getTableBodyProps()}>
                    {rows.map(row => {
                        prepareRow(row);
                        return (
                            <tr {...row.getRowProps()}>
                                {row.cells.map(cell => {
                                    return (
                                        <td
                                            {...cell.getCellProps()}
                                            style={{
                                                padding: '10px',
                                                border: 'solid 1px gray',
                                                background: 'papayawhip',
                                            }}
                                        >
                                            {cell.render('Cell')}
                                        </td>
                                    );
                                })}
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};

export default SymbolTable;